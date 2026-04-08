import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Chip,
  Switch,
  Dialog,
  Portal,
  Snackbar,
  ActivityIndicator,
  RadioButton,
  Divider,
  useTheme,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useStore, Account, BudgetItem } from '../store/store';
import { api } from '../api/api';
import HelpIcon from '../components/HelpIcon';

// ── Types ──────────────────────────────────────────────────────────────────

interface ParsedTransaction {
  date: string;
  amount: number;
  description: string;
}

interface MatchInfo {
  extrapolation_item_id: number;
  budget_item_name: string;
  scheduled_amount: number;
  due_date: string;
  confidence: number;
}

interface MatchResult {
  transaction: ParsedTransaction;
  match: MatchInfo | null;
  status: 'matched' | 'unmatched';
  included: boolean;  // local UI state
}

interface ParseResponse {
  headers: string[];
  detected_columns: { date: string; amount: string; description: string };
  transactions: ParsedTransaction[];
  count: number;
}

interface ImportResponse {
  imported: number;
  linked: number;
}

type Step = 'input' | 'review' | 'results';

// ── Component ──────────────────────────────────────────────────────────────

export default function ReconcileScreen() {
  const { selectedProfileId, accounts } = useStore();
  const theme = useTheme();

  // Step tracking
  const [step, setStep] = useState<Step>('input');

  // Step 1 — Input
  const [csvContent, setCsvContent] = useState('');
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [parsing, setParsing] = useState(false);

  // Step 2 — Review
  const [matchResults, setMatchResults] = useState<MatchResult[]>([]);
  const [matching, setMatching] = useState(false);
  const [importing, setImporting] = useState(false);

  // Step 2 — Reassign dialog
  const [reassignIndex, setReassignIndex] = useState<number | null>(null);
  const [reassignVisible, setReassignVisible] = useState(false);
  const [budgetItems, setBudgetItems] = useState<BudgetItem[]>([]);

  // Step 3 — Results
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);

  const [snackbar, setSnackbar] = useState('');

  // Fetch accounts when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      if (selectedProfileId && accounts.length > 0 && !selectedAccountId) {
        setSelectedAccountId(accounts[0].id);
      }
    }, [selectedProfileId, accounts, selectedAccountId])
  );

  // ── Step 1: Parse CSV ──────────────────────────────────────────────────

  const handleParse = async () => {
    if (!selectedProfileId || !selectedAccountId) {
      setSnackbar('Select an account first');
      return;
    }
    if (!csvContent.trim()) {
      setSnackbar('Paste CSV content first');
      return;
    }

    setParsing(true);
    try {
      // Step 1: Parse CSV
      const parsed = await api.post<ParseResponse>(
        `/reconcile/${selectedProfileId}/parse`,
        { csv_content: csvContent }
      );

      if (parsed.count === 0) {
        setSnackbar('No transactions found in CSV');
        setParsing(false);
        return;
      }

      // Step 2: Auto-match against budget
      setMatching(true);
      const matches = await api.post<MatchResult[]>(
        `/reconcile/${selectedProfileId}/match`,
        {
          transactions: parsed.transactions,
          account_id: selectedAccountId,
        }
      );

      // Add local UI state (included flag)
      setMatchResults(
        matches.map((m) => ({ ...m, included: true }))
      );

      // Fetch budget items for reassignment dialog
      try {
        const profile = await api.get<{ budget_items: BudgetItem[] }>(
          `/profiles/${selectedProfileId}`
        );
        setBudgetItems(profile.budget_items || []);
      } catch {
        // Non-critical — reassignment just won't have item names
      }

      setStep('review');
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to parse CSV');
    } finally {
      setParsing(false);
      setMatching(false);
    }
  };

  // ── Step 2: Toggle / Reassign ──────────────────────────────────────────

  const toggleInclude = (index: number) => {
    setMatchResults((prev) =>
      prev.map((m, i) => (i === index ? { ...m, included: !m.included } : m))
    );
  };

  const openReassign = (index: number) => {
    setReassignIndex(index);
    setReassignVisible(true);
  };

  const handleReassignClear = () => {
    if (reassignIndex === null) return;
    setMatchResults((prev) =>
      prev.map((m, i) =>
        i === reassignIndex
          ? { ...m, match: null, status: 'unmatched' as const }
          : m
      )
    );
    setReassignVisible(false);
    setReassignIndex(null);
  };

  // ── Step 2: Import Selected ────────────────────────────────────────────

  const handleImport = async () => {
    if (!selectedProfileId || !selectedAccountId) return;
    const selected = matchResults.filter((m) => m.included);
    if (selected.length === 0) {
      setSnackbar('No transactions selected');
      return;
    }

    setImporting(true);
    try {
      const confirmed = selected.map((m) => ({
        transaction: m.transaction,
        extrapolation_item_id: m.match?.extrapolation_item_id ?? null,
        amount_override: null,
      }));

      const result = await api.post<ImportResponse>(
        `/reconcile/${selectedProfileId}/import`,
        { account_id: selectedAccountId, confirmed }
      );

      setImportResult(result);
      setStep('results');
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to import transactions');
    } finally {
      setImporting(false);
    }
  };

  // ── Step 3: Done ───────────────────────────────────────────────────────

  const handleDone = () => {
    setCsvContent('');
    setMatchResults([]);
    setImportResult(null);
    setStep('input');
  };

  // ── Render helpers ─────────────────────────────────────────────────────

  const renderMatchItem = ({ item, index }: { item: MatchResult; index: number }) => {
    const isMatched = item.status === 'matched';

    return (
      <View style={styles.matchCard}>
        <View style={styles.matchHeader}>
          <View style={{ flex: 1 }}>
            <Text variant="bodyMedium" style={styles.matchDesc} numberOfLines={1}>
              {item.transaction.description || '(no description)'}
            </Text>
            <Text variant="bodySmall" style={styles.matchMeta}>
              {item.transaction.date}  ·  ${Math.abs(item.transaction.amount).toFixed(2)}
            </Text>
          </View>
          <Switch
            value={item.included}
            onValueChange={() => toggleInclude(index)}
            color={theme.colors.primary}
          />
        </View>

        <View style={styles.matchBody}>
          <Chip
            mode="flat"
            style={isMatched ? styles.chipMatched : styles.chipUnmatched}
            textStyle={isMatched ? styles.chipMatchedText : styles.chipUnmatchedText}
            compact
          >
            {isMatched ? 'Matched' : 'Unmatched'}
          </Chip>

          {isMatched && item.match && (
            <Text variant="bodySmall" style={styles.matchDetail}>
              {item.match.budget_item_name} · {item.match.confidence}%
            </Text>
          )}
        </View>

        <Button
          mode="text"
          compact
          onPress={() => openReassign(index)}
          style={styles.reassignButton}
          labelStyle={styles.reassignLabel}
        >
          {isMatched ? 'Change Match' : 'Assign Match'}
        </Button>
      </View>
    );
  };

  // ── Main Render ────────────────────────────────────────────────────────

  if (!selectedProfileId) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
        <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
          <Text variant="titleLarge" style={styles.title}>Reconcile</Text>
          <Text variant="bodyMedium" style={styles.emptyText}>
            Select a profile in Settings to reconcile bank transactions
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
          <Text variant="titleLarge">Reconcile</Text>
          <HelpIcon text="Import bank CSV statements and match transactions against your budget to find discrepancies." />
        </View>

        {/* ── Step 1: Input CSV ──────────────────────────────────────────── */}
        {step === 'input' && (
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={{ flex: 1 }}
          >
            <ScrollView style={{ flex: 1 }} keyboardShouldPersistTaps="handled">
              <Text variant="titleSmall" style={[styles.sectionTitle, { color: theme.colors.primary }]}>
                1. Select Account
              </Text>
              <RadioButton.Group
                value={String(selectedAccountId ?? '')}
                onValueChange={(v) => setSelectedAccountId(parseInt(v, 10))}
              >
                {accounts.map((acct: Account) => (
                  <RadioButton.Item
                    key={acct.id}
                    label={`${acct.name} ($${acct.balance.toFixed(2)})`}
                    value={String(acct.id)}
                    color={theme.colors.primary}
                    labelStyle={styles.radioLabel}
                    style={styles.radioItem}
                  />
                ))}
              </RadioButton.Group>

              {accounts.length === 0 && (
                <Text variant="bodySmall" style={styles.emptyText}>
                  No accounts found. Add accounts first.
                </Text>
              )}

              <Text variant="titleSmall" style={[styles.sectionTitle, { marginTop: 16 }]}>
                2. Paste CSV Content
              </Text>
              <TextInput
                mode="outlined"
                placeholder="Paste bank CSV here..."
                value={csvContent}
                onChangeText={setCsvContent}
                multiline
                numberOfLines={10}
                style={styles.csvInput}
              />

              <Button
                mode="contained"
                onPress={handleParse}
                loading={parsing || matching}
                disabled={parsing || matching || !csvContent.trim() || !selectedAccountId}
                style={styles.parseButton}
                icon="file-search"
              >
                {matching ? 'Matching...' : parsing ? 'Parsing...' : 'Parse & Match'}
              </Button>
            </ScrollView>
          </KeyboardAvoidingView>
        )}

        {/* ── Step 2: Review Matches ────────────────────────────────────── */}
        {step === 'review' && (
          <View style={{ flex: 1 }}>
            <View style={styles.reviewHeader}>
              <Text variant="bodyMedium">
                {matchResults.filter((m) => m.status === 'matched').length} matched
                {' · '}
                {matchResults.filter((m) => m.status === 'unmatched').length} unmatched
                {' · '}
                {matchResults.filter((m) => m.included).length} selected
              </Text>
              <Button
                mode="text"
                compact
                onPress={() => setStep('input')}
                labelStyle={{ fontSize: 12 }}
              >
                Back
              </Button>
            </View>

            <FlatList
              data={matchResults}
              keyExtractor={(_, i) => String(i)}
              renderItem={renderMatchItem}
              ItemSeparatorComponent={() => <Divider style={styles.divider} />}
              style={{ flex: 1 }}
            />

            <Button
              mode="contained"
              onPress={handleImport}
              loading={importing}
              disabled={importing || matchResults.filter((m) => m.included).length === 0}
              style={styles.importButton}
              icon="database-import"
            >
              Import Selected ({matchResults.filter((m) => m.included).length})
            </Button>
          </View>
        )}

        {/* ── Step 3: Results ───────────────────────────────────────────── */}
        {step === 'results' && importResult && (
          <View style={styles.resultsContainer}>
            <Text variant="headlineMedium" style={[styles.resultsTitle, { color: theme.colors.primary }]}>
              Import Complete
            </Text>
            <View style={styles.resultsStat}>
              <Text variant="displaySmall" style={[styles.resultsNumber, { color: theme.colors.primary }]}>
                {importResult.imported}
              </Text>
              <Text variant="bodyMedium" style={styles.resultsLabel}>
                transactions imported
              </Text>
            </View>
            <View style={styles.resultsStat}>
              <Text variant="displaySmall" style={[styles.resultsNumber, { color: theme.colors.primary }]}>
                {importResult.linked}
              </Text>
              <Text variant="bodyMedium" style={styles.resultsLabel}>
                linked to budget items
              </Text>
            </View>
            <Button
              mode="contained"
              onPress={handleDone}
              style={styles.doneButton}
              icon="check"
            >
              Done
            </Button>
          </View>
        )}
      </View>

      {/* ── Reassign Match Dialog ──────────────────────────────────────── */}
      <Portal>
        <Dialog
          visible={reassignVisible}
          onDismiss={() => { setReassignVisible(false); setReassignIndex(null); }}
        >
          <Dialog.Title>Reassign Match</Dialog.Title>
          <Dialog.ScrollArea style={styles.reassignScroll}>
            <ScrollView>
              {reassignIndex !== null && (
                <View>
                  <Text variant="bodySmall" style={{ marginBottom: 12, opacity: 0.7 }}>
                    {matchResults[reassignIndex]?.transaction.description}
                    {' · $'}
                    {Math.abs(matchResults[reassignIndex]?.transaction.amount ?? 0).toFixed(2)}
                  </Text>

                  <Button
                    mode="outlined"
                    onPress={handleReassignClear}
                    style={{ marginBottom: 16 }}
                    icon="close"
                  >
                    Clear Match (Unmatched)
                  </Button>

                  <Divider style={{ marginBottom: 12 }} />
                  <Text variant="titleSmall" style={{ marginBottom: 8, color: theme.colors.primary }}>
                    Budget Items
                  </Text>

                  {budgetItems.length === 0 && (
                    <Text variant="bodySmall" style={styles.emptyText}>
                      No budget items available
                    </Text>
                  )}

                  {budgetItems.map((bi) => (
                    <Button
                      key={bi.id}
                      mode="text"
                      compact
                      onPress={() => {
                        if (reassignIndex === null) return;
                        setMatchResults((prev) =>
                          prev.map((m, i) =>
                            i === reassignIndex
                              ? {
                                  ...m,
                                  match: {
                                    extrapolation_item_id: 0, // no extrap link — standalone
                                    budget_item_name: bi.name,
                                    scheduled_amount: bi.amount,
                                    due_date: m.transaction.date,
                                    confidence: 100,
                                  },
                                  status: 'matched' as const,
                                }
                              : m
                          )
                        );
                        setReassignVisible(false);
                        setReassignIndex(null);
                      }}
                      style={styles.budgetItemButton}
                      labelStyle={styles.budgetItemLabel}
                    >
                      {bi.name} (${bi.amount.toFixed(2)})
                    </Button>
                  ))}
                </View>
              )}
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => { setReassignVisible(false); setReassignIndex(null); }}>
              Cancel
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={2000}>
        {snackbar}
      </Snackbar>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  title: { marginBottom: 16 },
  sectionTitle: { marginBottom: 8 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  radioLabel: { fontSize: 14 },
  radioItem: { paddingVertical: 2 },
  csvInput: {
    minHeight: 160,
    fontSize: 12,
    marginBottom: 16,
  },
  parseButton: { marginTop: 4, marginBottom: 24 },

  // Review step
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  matchCard: {
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  matchHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  matchDesc: { fontWeight: '600' },
  matchMeta: { opacity: 0.7, marginTop: 2 },
  matchBody: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  chipMatched: { backgroundColor: '#1b5e20' },
  chipMatchedText: { color: '#a5d6a7', fontSize: 12 },
  chipUnmatched: { backgroundColor: '#e65100' },
  chipUnmatchedText: { color: '#ffcc80', fontSize: 12 },
  matchDetail: { opacity: 0.8, fontSize: 12 },
  reassignButton: { alignSelf: 'flex-start', marginTop: 2 },
  reassignLabel: { fontSize: 12 },
  divider: { opacity: 0.3 },
  importButton: { marginTop: 12, marginBottom: 8 },

  // Results step
  resultsContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  resultsTitle: { marginBottom: 32 },
  resultsStat: { alignItems: 'center', marginBottom: 24 },
  resultsNumber: { fontWeight: '700' },
  resultsLabel: { opacity: 0.7, marginTop: 4 },
  doneButton: { marginTop: 24, paddingHorizontal: 32 },

  // Reassign dialog
  reassignScroll: { maxHeight: 400 },
  budgetItemButton: { justifyContent: 'flex-start', paddingVertical: 2 },
  budgetItemLabel: { fontSize: 13 },
});
