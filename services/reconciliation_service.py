"""
Reconciliation Service — Import bank CSV, auto-match to budget items.
"""

import csv
import io
from datetime import date, datetime
from database.database import Database


class ReconciliationService:
    """Service for bank ledger import and reconciliation."""

    # Common CSV column name patterns for auto-detection
    DATE_PATTERNS = ['date', 'posted', 'transaction date', 'post date', 'posting date']
    AMOUNT_PATTERNS = ['amount', 'debit', 'credit', 'transaction amount']
    DESC_PATTERNS = ['description', 'memo', 'narrative', 'details', 'payee', 'name']

    def __init__(self, db: Database):
        self.db = db

    def parse_csv(self, csv_content: str, date_col: str = None, amount_col: str = None, desc_col: str = None) -> dict:
        """
        Parse a bank CSV and return structured transactions + detected columns.
        If column names not specified, auto-detect from headers.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        headers = reader.fieldnames or []

        # Auto-detect columns if not specified
        if not date_col:
            date_col = self._detect_column(headers, self.DATE_PATTERNS)
        if not amount_col:
            amount_col = self._detect_column(headers, self.AMOUNT_PATTERNS)
        if not desc_col:
            desc_col = self._detect_column(headers, self.DESC_PATTERNS)

        transactions = []
        for row in reader:
            try:
                raw_date = row.get(date_col, '').strip()
                raw_amount = row.get(amount_col, '').strip()
                description = row.get(desc_col, '').strip()

                if not raw_date or not raw_amount:
                    continue

                # Parse date (try common formats)
                parsed_date = self._parse_date(raw_date)
                if not parsed_date:
                    continue

                # Parse amount (handle parentheses for negatives, remove $, commas)
                parsed_amount = self._parse_amount(raw_amount)
                if parsed_amount is None:
                    continue

                transactions.append({
                    'date': parsed_date.isoformat(),
                    'amount': parsed_amount,
                    'description': description,
                })
            except Exception:
                continue  # Skip unparseable rows

        return {
            'headers': headers,
            'detected_columns': {
                'date': date_col,
                'amount': amount_col,
                'description': desc_col,
            },
            'transactions': transactions,
            'count': len(transactions),
        }

    def match_transactions(self, profile_id: int, transactions: list, account_id: int, date_tolerance_days: int = 5, amount_tolerance_pct: float = 0.10) -> list:
        """
        Match parsed transactions against unpaid extrapolation items.

        Returns a list of proposed matches:
        {
            'transaction': {date, amount, description},
            'match': {extrapolation_item_id, budget_item_name, scheduled_amount, due_date, confidence} or None,
            'status': 'matched' | 'unmatched'
        }
        """
        # Get unpaid extrapolation items (no ledger_entry_id)
        all_items = self.db.fetch_extrapolation_items(profile_id)
        unpaid = [item for item in all_items if item.ledger_entry_id is None and item.income_date is not None]

        # Get budget items for names
        budget_items = {bi.id: bi for bi in self.db.fetch_budget_items(profile_id)}

        # Track which extrapolation items have been matched (prevent double-match)
        matched_item_ids = set()

        results = []
        for txn in transactions:
            txn_date = date.fromisoformat(txn['date'])
            txn_amount = txn['amount']

            best_match = None
            best_score = 0

            for item in unpaid:
                if item.id in matched_item_ids:
                    continue

                # Compare amounts (bank transactions are usually positive for debits,
                # extrapolation expenses are negative)
                item_amount = abs(float(item.amount))
                txn_abs = abs(txn_amount)

                if item_amount == 0:
                    continue

                amount_diff_pct = abs(item_amount - txn_abs) / item_amount
                if amount_diff_pct > amount_tolerance_pct:
                    continue  # Too far off

                # Compare dates
                item_due = item.due_date if isinstance(item.due_date, date) else date.fromisoformat(str(item.due_date))
                date_diff = abs((txn_date - item_due).days)
                if date_diff > date_tolerance_days:
                    continue  # Too far in time

                # Score: lower is better (amount accuracy + date proximity)
                # amount_diff_pct is 0-tolerance, date_diff is 0-tolerance
                # Normalize both to 0-1 range and combine
                amount_score = 1.0 - (amount_diff_pct / amount_tolerance_pct)
                date_score = 1.0 - (date_diff / date_tolerance_days)
                score = (amount_score * 0.6) + (date_score * 0.4)

                if score > best_score:
                    best_score = score
                    bi = budget_items.get(item.budget_item_id)
                    best_match = {
                        'extrapolation_item_id': item.id,
                        'budget_item_name': bi.name if bi else (getattr(item, 'category', None) or 'Unknown'),
                        'scheduled_amount': float(item.amount),
                        'due_date': item_due.isoformat(),
                        'confidence': round(score * 100),
                    }

            if best_match:
                matched_item_ids.add(best_match['extrapolation_item_id'])
                results.append({
                    'transaction': txn,
                    'match': best_match,
                    'status': 'matched',
                })
            else:
                results.append({
                    'transaction': txn,
                    'match': None,
                    'status': 'unmatched',
                })

        return results

    def import_confirmed(self, profile_id: int, account_id: int, confirmed: list) -> dict:
        """
        Import confirmed matches. Each item in confirmed is:
        {
            'transaction': {date, amount, description},
            'extrapolation_item_id': int or None,
            'amount_override': float or None (use transaction amount if None)
        }

        Creates ledger entries and links to extrapolation items where applicable.
        """
        from services.ledger_service import LedgerService
        ledger_service = LedgerService(self.db)

        imported = 0
        linked = 0

        for item in confirmed:
            txn = item['transaction']
            extrap_id = item.get('extrapolation_item_id')
            amount = item.get('amount_override') or txn['amount']

            txn_date = txn['date']

            if extrap_id:
                # Link to extrapolation item (mark paid)
                try:
                    ledger_service.mark_extrapolation_item_paid(
                        extrapolation_item_id=extrap_id,
                        account_id=account_id,
                        paid_date=txn_date,
                    )
                    linked += 1
                    imported += 1
                except ValueError:
                    # Already paid or not found — create standalone entry
                    ledger_service.create_ledger_entry(
                        account_id=account_id,
                        amount=amount,
                        paid_date=txn_date,
                        income_date=txn_date,
                        name=txn.get('description', 'Bank Import'),
                    )
                    imported += 1
            else:
                # Standalone transaction (no budget match)
                ledger_service.create_ledger_entry(
                    account_id=account_id,
                    amount=amount,
                    paid_date=txn_date,
                    income_date=txn_date,
                    name=txn.get('description', 'Bank Import'),
                )
                imported += 1

        return {'imported': imported, 'linked': linked}

    def _detect_column(self, headers: list, patterns: list) -> str | None:
        """Find a header matching common patterns (case-insensitive)."""
        lower_headers = {h.lower().strip(): h for h in headers}
        for pattern in patterns:
            if pattern in lower_headers:
                return lower_headers[pattern]
        # Partial match
        for pattern in patterns:
            for lh, original in lower_headers.items():
                if pattern in lh:
                    return original
        return headers[0] if headers else None  # fallback to first column

    def _parse_date(self, raw: str) -> date | None:
        """Try multiple date formats."""
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_amount(self, raw: str) -> float | None:
        """Parse amount string, handling $, commas, parentheses for negatives."""
        raw = raw.replace('$', '').replace(',', '').strip()
        # Parentheses = negative: (100.00) -> -100.00
        if raw.startswith('(') and raw.endswith(')'):
            raw = '-' + raw[1:-1]
        try:
            return float(raw)
        except ValueError:
            return None
