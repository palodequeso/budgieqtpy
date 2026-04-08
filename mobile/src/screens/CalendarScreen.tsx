import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
  Linking,
} from 'react-native';
import {
  Text,
  ActivityIndicator,
  Badge,
  Button,
  Dialog,
  Portal,
  Snackbar,
  SegmentedButtons,
  TextInput,
  Switch,
  RadioButton,
  List,
  Divider,
  IconButton,
  useTheme,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useStore, Account, BudgetItem, ExtrapolationItem } from '../store/store';
import { api } from '../api/api';

// ─── Simple Markdown Renderer ─────────────────────────────────────────────────

function SimpleMarkdown({ text }: { text: string }) {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const key = `md-${i}`;

    // Headers
    if (line.startsWith('### ')) {
      elements.push(<Text key={key} style={{ fontWeight: 'bold', fontSize: 15, marginTop: 12, marginBottom: 4 }}>{renderInline(line.slice(4))}</Text>);
    } else if (line.startsWith('## ')) {
      elements.push(<Text key={key} style={{ fontWeight: 'bold', fontSize: 17, marginTop: 14, marginBottom: 4 }}>{renderInline(line.slice(3))}</Text>);
    } else if (line.startsWith('# ')) {
      elements.push(<Text key={key} style={{ fontWeight: 'bold', fontSize: 19, marginTop: 16, marginBottom: 6 }}>{renderInline(line.slice(2))}</Text>);
    }
    // Bullet lists
    else if (/^[-*] /.test(line)) {
      elements.push(<Text key={key} style={{ marginLeft: 12, lineHeight: 22 }}>  {'\u2022'}  {renderInline(line.slice(2))}</Text>);
    }
    // Numbered lists
    else if (/^\d+\. /.test(line)) {
      const match = line.match(/^(\d+)\. (.*)$/);
      if (match) {
        elements.push(<Text key={key} style={{ marginLeft: 12, lineHeight: 22 }}>  {match[1]}.  {renderInline(match[2])}</Text>);
      }
    }
    // Horizontal rule
    else if (line.trim() === '---') {
      elements.push(<View key={key} style={{ borderBottomWidth: 1, borderBottomColor: '#555', marginVertical: 8 }} />);
    }
    // Empty line
    else if (line.trim() === '') {
      elements.push(<View key={key} style={{ height: 8 }} />);
    }
    // Regular text
    else {
      elements.push(<Text key={key} style={{ lineHeight: 22 }}>{renderInline(line)}</Text>);
    }
  }

  return <View>{elements}</View>;
}

function renderInline(text: string): React.ReactNode {
  // Split on **bold** and *italic* patterns
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      parts.push(<Text key={match.index} style={{ fontWeight: 'bold', fontStyle: 'italic' }}>{match[2]}</Text>);
    } else if (match[3]) {
      parts.push(<Text key={match.index} style={{ fontWeight: 'bold' }}>{match[3]}</Text>);
    } else if (match[4]) {
      parts.push(<Text key={match.index} style={{ fontStyle: 'italic' }}>{match[4]}</Text>);
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length === 1 && typeof parts[0] === 'string' ? parts[0] : <>{parts}</>;
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface ScheduleResponse {
  extrapolation_items: ExtrapolationItem[];
}

interface ProfileResponse {
  id: number;
  name: string;
  accounts: Account[];
  budget_items: BudgetItem[];
  budget_groups: any[];
}

interface SavingsEntry {
  date: string;
  amount: number;
}

interface IncomeColumn {
  date: string;
  items: ExtrapolationItem[];
  incomeTotal: number;
  expenseTotal: number;
  carryForward: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const todayStr = () => new Date().toISOString().slice(0, 10);
const oneYearFromNow = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() + 1);
  return d.toISOString().slice(0, 10);
};

function formatDateHeader(dateStr: string): string {
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
}

const SCREEN_WIDTH = Dimensions.get('window').width;

// ─── Component ────────────────────────────────────────────────────────────────

export default function CalendarScreen() {
  const { selectedProfileId } = useStore();
  const theme = useTheme();

  // ── Data state ──────────────────────────────────────────────────────────────
  const [scheduleItems, setScheduleItems] = useState<ExtrapolationItem[]>([]);
  const [budgetItems, setBudgetItems] = useState<BudgetItem[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState('');

  // ── Tab state ───────────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<'schedule' | 'actions'>('schedule');

  // ── Column pager state ───────────────────────────────────────────────────────
  const flatListRef = useRef<FlatList<IncomeColumn>>(null);
  const [columnIndex, setColumnIndex] = useState(0);

  // ── Item detail dialog ───────────────────────────────────────────────────────
  const [selectedItem, setSelectedItem] = useState<ExtrapolationItem | null>(null);
  const [itemDetailVisible, setItemDetailVisible] = useState(false);
  const [itemAccountId, setItemAccountId] = useState<number | null>(null);
  const [markingItemPaid, setMarkingItemPaid] = useState(false);

  // ── Move item dialog ──────────────────────────────────────────────────────────
  const [moveDialogVisible, setMoveDialogVisible] = useState(false);
  const [moveItem, setMoveItem] = useState<{budget_item_id: number, from_income_date: string, name: string, amount: number} | null>(null);
  const [movingItem, setMovingItem] = useState(false);

  // ── Split item dialog ─────────────────────────────────────────────────────────
  const [splitDialogVisible, setSplitDialogVisible] = useState(false);
  const [splitItem, setSplitItem] = useState<ExtrapolationItem | null>(null);
  const [splitKeepAmount, setSplitKeepAmount] = useState('');
  const [splitDestDate, setSplitDestDate] = useState('');
  const [splittingItem, setSplittingItem] = useState(false);

  // ── One-off form ────────────────────────────────────────────────────────────
  const [oneOffName, setOneOffName] = useState('');
  const [oneOffAmount, setOneOffAmount] = useState('');
  const [oneOffType, setOneOffType] = useState<'expense' | 'income'>('expense');
  const [oneOffDate, setOneOffDate] = useState(todayStr);
  const [oneOffAccountId, setOneOffAccountId] = useState<number | null>(null);
  const [oneOffPaid, setOneOffPaid] = useState(false);
  const [savingOneOff, setSavingOneOff] = useState(false);
  const [oneOffAccountPickerVisible, setOneOffAccountPickerVisible] = useState(false);

  // ── Compute savings ─────────────────────────────────────────────────────────
  const [savingsAccountId, setSavingsAccountId] = useState<number | null>(null);
  const [spendingBuffer, setSpendingBuffer] = useState('0');
  const [computing, setComputing] = useState(false);
  const [computedEntries, setComputedEntries] = useState<SavingsEntry[] | null>(null);
  const [savingComputed, setSavingComputed] = useState(false);
  const [computeConfirmVisible, setComputeConfirmVisible] = useState(false);
  const [savingsAccountPickerVisible, setSavingsAccountPickerVisible] = useState(false);

  // ── Got Paid ─────────────────────────────────────────────────────────────────
  const [gotPaidVisible, setGotPaidVisible] = useState(false);
  const [gotPaidAccountId, setGotPaidAccountId] = useState<number | null>(null);
  const [gotPaidItemId, setGotPaidItemId] = useState<number | null>(null);
  const [markingPaid, setMarkingPaid] = useState(false);

  // ── Extrapolation ───────────────────────────────────────────────────────────
  const [extrapolateDialogVisible, setExtrapolateDialogVisible] = useState(false);
  const [extrapolateStart, setExtrapolateStart] = useState(todayStr);
  const [extrapolateEnd, setExtrapolateEnd] = useState(oneYearFromNow);
  const [extrapolating, setExtrapolating] = useState(false);

  // ── Fix unscheduled ─────────────────────────────────────────────────────────
  const [fixDialogVisible, setFixDialogVisible] = useState(false);
  const [unscheduledDates, setUnscheduledDates] = useState<Record<number, string>>({});
  const [fixing, setFixing] = useState(false);

  // ── AI Analysis ────────────────────────────────────────────────────────────
  const [aiAnalysisVisible, setAiAnalysisVisible] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  // ── Long-press mark paid state ──────────────────────────────────────────────
  const [longPressMarkingId, setLongPressMarkingId] = useState<number | null>(null);

  // ── Derived ─────────────────────────────────────────────────────────────────
  const budgetItemMap = useMemo(
    () => Object.fromEntries(budgetItems.map((item) => [item.id, item])),
    [budgetItems]
  );

  const isIncomeItem = useCallback(
    (item: ExtrapolationItem) =>
      item.budget_item_id != null &&
      budgetItemMap[item.budget_item_id]?.type?.toLowerCase() === 'income',
    [budgetItemMap]
  );

  const getItemName = useCallback(
    (item: ExtrapolationItem): string => {
      if (item.budget_item_id != null && budgetItemMap[item.budget_item_id]) {
        return budgetItemMap[item.budget_item_id].name;
      }
      return item.category ?? 'One-off item';
    },
    [budgetItemMap]
  );

  // Build income columns from schedule items
  const incomeColumns = useMemo<IncomeColumn[]>(() => {
    const map: Record<string, ExtrapolationItem[]> = {};
    for (const item of scheduleItems) {
      if (!item.income_date) continue;
      const key = item.income_date.slice(0, 10);
      if (!map[key]) map[key] = [];
      map[key].push(item);
    }
    const sorted = Object.entries(map).sort(([a], [b]) => a.localeCompare(b));
    let running = 0;
    return sorted.map(([date, items]) => {
      const incomeTotal = items
        .filter((i) => i.budget_item_id != null && budgetItemMap[i.budget_item_id]?.type?.toLowerCase() === 'income')
        .reduce((s, i) => s + i.amount, 0);
      const expenseTotal = items
        .filter((i) => !(i.budget_item_id != null && budgetItemMap[i.budget_item_id]?.type?.toLowerCase() === 'income'))
        .reduce((s, i) => s + Math.abs(i.amount), 0);
      const carryForward = running;
      running += incomeTotal - expenseTotal;
      return { date, items, incomeTotal, expenseTotal, carryForward };
    });
  }, [scheduleItems, budgetItemMap]);

  const unscheduledItems = useMemo(
    () => scheduleItems.filter((item) => !item.income_date),
    [scheduleItems]
  );

  const unpaidIncomeItems = useMemo(
    () =>
      scheduleItems.filter(
        (item) =>
          item.ledger_entry_id === null &&
          item.income_date !== null &&
          isIncomeItem(item)
      ),
    [scheduleItems, isIncomeItem]
  );

  const fixAllDatesSelected = Object.values(unscheduledDates).every((d) => d.length === 10);

  // Column pager width — parent container has 16px padding each side
  const COLUMN_WIDTH = SCREEN_WIDTH - 32;

  // Index of the "current period" column (nearest to today)
  const currentPeriodIndex = useMemo(() => {
    if (incomeColumns.length === 0) return -1;
    const today = todayStr();
    let idx = incomeColumns.findIndex((c) => c.date >= today);
    if (idx === -1) idx = incomeColumns.length - 1;
    return idx;
  }, [incomeColumns]);

  // Jump to nearest/current column when data first loads
  useEffect(() => {
    if (incomeColumns.length === 0) return;
    setColumnIndex(currentPeriodIndex);
    setTimeout(() => {
      flatListRef.current?.scrollToIndex({ index: currentPeriodIndex, animated: false });
    }, 80);
  }, [incomeColumns.length]); // only on length change (initial load / extrapolation)

  // ── Data fetching ────────────────────────────────────────────────────────────
  const fetchData = useCallback(
    async (isRefresh = false) => {
      if (!selectedProfileId) return;
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const [profile, schedule] = await Promise.all([
          api.get<ProfileResponse>(`/profiles/${selectedProfileId}`),
          api.get<ScheduleResponse>(`/schedule/${selectedProfileId}`),
        ]);
        setBudgetItems(profile.budget_items);
        setAccounts(profile.accounts);
        setScheduleItems(schedule.extrapolation_items);
      } catch (e: any) {
        setError(e.message ?? 'Failed to load calendar');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [selectedProfileId]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Column navigation ────────────────────────────────────────────────────────
  const goToPrevColumn = () => {
    const next = Math.max(0, columnIndex - 1);
    setColumnIndex(next);
    flatListRef.current?.scrollToIndex({ index: next, animated: true });
  };

  const goToNextColumn = () => {
    const next = Math.min(incomeColumns.length - 1, columnIndex + 1);
    setColumnIndex(next);
    flatListRef.current?.scrollToIndex({ index: next, animated: true });
  };

  // ── Item tap ─────────────────────────────────────────────────────────────────
  const handleItemTap = (item: ExtrapolationItem) => {
    setSelectedItem(item);
    setItemAccountId(accounts[0]?.id ?? null);
    setItemDetailVisible(true);
  };

  // ── Long-press quick mark paid ───────────────────────────────────────────────
  const handleLongPressPaid = async (item: ExtrapolationItem) => {
    // Ignore if already paid or no profile/accounts
    if (item.ledger_entry_id !== null || !selectedProfileId || accounts.length === 0) return;
    const defaultAccountId = accounts[0].id;
    setLongPressMarkingId(item.id);
    try {
      await api.post(`/budget/markpaid/${selectedProfileId}`, {
        extrapolationItemId: item.id,
        accountId: defaultAccountId,
      });
      setSnackbar(`Marked ${getItemName(item)} as paid`);
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to mark as paid');
    } finally {
      setLongPressMarkingId(null);
    }
  };

  const handleMarkItemReceived = async () => {
    if (!selectedProfileId || !selectedItem || itemAccountId == null) return;
    setMarkingItemPaid(true);
    try {
      await api.post(`/budget/markpaid/${selectedProfileId}`, {
        extrapolationItemId: selectedItem.id,
        accountId: itemAccountId,
      });
      setItemDetailVisible(false);
      setSnackbar('Income marked as received');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to mark income');
    } finally {
      setMarkingItemPaid(false);
    }
  };

  // ── Handlers: move item ──────────────────────────────────────────────────────
  const openMoveDialog = (item: ExtrapolationItem) => {
    if (item.budget_item_id == null || !item.income_date) return;
    setMoveItem({
      budget_item_id: item.budget_item_id,
      from_income_date: item.income_date.slice(0, 10),
      name: getItemName(item),
      amount: Math.abs(item.amount),
    });
    setItemDetailVisible(false);
    setMoveDialogVisible(true);
  };

  const handleMoveItem = async (toDate: string) => {
    if (!moveItem || !selectedProfileId) return;
    setMovingItem(true);
    try {
      await api.post(`/calendar/${selectedProfileId}/move_item`, {
        budget_item_id: moveItem.budget_item_id,
        from_income_date: moveItem.from_income_date,
        to_income_date: toDate,
      });
      setMoveDialogVisible(false);
      setMoveItem(null);
      setSnackbar('Item moved');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to move item');
    } finally {
      setMovingItem(false);
    }
  };

  // ── Handlers: split item ─────────────────────────────────────────────────────
  const openSplitDialog = (item: ExtrapolationItem) => {
    setSplitItem(item);
    setSplitKeepAmount((Math.abs(item.amount) / 2).toFixed(2));
    // Default to first column that isn't the item's current column
    const otherCol = incomeColumns.find((c) => c.date !== item.income_date?.slice(0, 10));
    setSplitDestDate(otherCol?.date ?? incomeColumns[0]?.date ?? '');
    setItemDetailVisible(false);
    setSplitDialogVisible(true);
  };

  const handleSplitItem = async () => {
    if (!selectedProfileId || !splitItem || !splitDestDate) return;
    const keepAmt = parseFloat(splitKeepAmount);
    if (isNaN(keepAmt) || keepAmt <= 0 || keepAmt >= Math.abs(splitItem.amount)) {
      setSnackbar('Keep amount must be between 0 and the total');
      return;
    }
    setSplittingItem(true);
    try {
      await api.post(`/calendar/${selectedProfileId}/split_item`, {
        extrapolation_item_id: splitItem.id,
        keep_amount: keepAmt,
        remainder_income_date: splitDestDate,
      });
      setSplitDialogVisible(false);
      setSplitItem(null);
      setSnackbar('Item split');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to split item');
    } finally {
      setSplittingItem(false);
    }
  };

  // ── Handlers: one-off ────────────────────────────────────────────────────────
  const handleAddOneOff = async () => {
    if (!selectedProfileId) return;
    if (!oneOffName.trim()) { setSnackbar('Name is required'); return; }
    if (!oneOffAmount || isNaN(parseFloat(oneOffAmount))) { setSnackbar('Amount must be a number'); return; }
    if (!oneOffDate || oneOffDate.length !== 10) { setSnackbar('Date must be YYYY-MM-DD'); return; }
    setSavingOneOff(true);
    try {
      await api.post(`/calendar/${selectedProfileId}/oneoff`, {
        name: oneOffName.trim(),
        amount: parseFloat(oneOffAmount),
        type: oneOffType,
        incomeDate: oneOffDate,
        account: oneOffAccountId ?? undefined,
        addingOneOffExpensePaid: oneOffPaid,
      });
      setOneOffName('');
      setOneOffAmount('');
      setOneOffType('expense');
      setOneOffDate(todayStr());
      setOneOffAccountId(null);
      setOneOffPaid(false);
      setSnackbar('One-off item added');
      setActiveTab('schedule');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to add one-off item');
    } finally {
      setSavingOneOff(false);
    }
  };

  // ── Handlers: compute savings ────────────────────────────────────────────────
  const handleComputeSavings = async () => {
    if (!selectedProfileId || savingsAccountId == null) {
      setSnackbar('Select a savings account first');
      return;
    }
    setComputing(true);
    try {
      const result = await api.post<{ addedEntries: SavingsEntry[] }>(
        `/calendar/${selectedProfileId}/computesavings`,
        { savingsAccount: savingsAccountId, spendingBuffer: parseFloat(spendingBuffer) || 0 }
      );
      if (!result.addedEntries || result.addedEntries.length === 0) {
        setSnackbar('No savings entries found');
        return;
      }
      setComputedEntries(result.addedEntries);
      setComputeConfirmVisible(true);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to compute savings');
    } finally {
      setComputing(false);
    }
  };

  const handleSaveComputedSavings = async () => {
    if (!selectedProfileId || !computedEntries || savingsAccountId == null) return;
    setSavingComputed(true);
    try {
      await api.post(`/calendar/${selectedProfileId}/savecomputedsavings`, {
        addedEntries: computedEntries,
        savingsAccount: savingsAccountId,
      });
      setComputeConfirmVisible(false);
      setComputedEntries(null);
      setSnackbar(`Saved ${computedEntries.length} savings entries`);
      setActiveTab('schedule');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save savings entries');
    } finally {
      setSavingComputed(false);
    }
  };

  // ── Handlers: extrapolation ───────────────────────────────────────────────────
  const handleRunExtrapolation = async () => {
    if (!selectedProfileId) return;
    setExtrapolating(true);
    try {
      const result = await api.post<{ success: boolean; count: number }>(
        `/extrapolate/${selectedProfileId}`,
        {
          profileID: selectedProfileId,
          start_date: extrapolateStart || undefined,
          end_date: extrapolateEnd || undefined,
        }
      );
      setExtrapolateDialogVisible(false);
      setSnackbar(`Extrapolation complete — ${result.count} items scheduled`);
      setActiveTab('schedule');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Extrapolation failed');
    } finally {
      setExtrapolating(false);
    }
  };

  // ── Handlers: got paid ───────────────────────────────────────────────────────
  const openGotPaid = () => {
    if (unpaidIncomeItems.length === 0) { setSnackbar('No unpaid income items found'); return; }
    setGotPaidItemId(unpaidIncomeItems[0].id);
    setGotPaidAccountId(accounts[0]?.id ?? null);
    setGotPaidVisible(true);
  };

  const handleGotPaid = async () => {
    if (!selectedProfileId || gotPaidItemId == null || gotPaidAccountId == null) return;
    setMarkingPaid(true);
    try {
      await api.post(`/budget/markpaid/${selectedProfileId}`, {
        extrapolationItemId: gotPaidItemId,
        accountId: gotPaidAccountId,
      });
      setGotPaidVisible(false);
      setSnackbar('Income marked as received');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to mark income');
    } finally {
      setMarkingPaid(false);
    }
  };

  // ── Handlers: fix unscheduled ────────────────────────────────────────────────
  const openFixDialog = () => {
    const dates: Record<number, string> = {};
    unscheduledItems.forEach((item) => { dates[item.id] = todayStr(); });
    setUnscheduledDates(dates);
    setFixDialogVisible(true);
  };

  const handleFixUnscheduled = async () => {
    if (!selectedProfileId) return;
    setFixing(true);
    try {
      const items = unscheduledItems.map((item) => ({
        id: item.id,
        income_date: unscheduledDates[item.id],
      }));
      await api.post(`/calendar/${selectedProfileId}/fixunscheduled`, items);
      setFixDialogVisible(false);
      setSnackbar('Unscheduled items updated');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to fix unscheduled items');
    } finally {
      setFixing(false);
    }
  };

  // ── Handlers: AI analysis ──────────────────────────────────────────────────
  const handleAiAnalysis = async () => {
    if (!selectedProfileId) return;
    setAiLoading(true);
    setAiAnalysis(null);
    setAiError(null);
    setAiAnalysisVisible(true);
    try {
      const result = await api.post<{ analysis?: string; error?: string }>(`/ai/analyze/${selectedProfileId}`, {});
      if (result.error) {
        setAiError(result.error);
      } else {
        setAiAnalysis(result.analysis ?? null);
      }
    } catch (e: any) {
      setAiError(e.message || 'Failed to run AI analysis');
    } finally {
      setAiLoading(false);
    }
  };

  const handleDownloadSpreadsheet = () => {
    if (!selectedProfileId) return;
    const baseUrl = useStore.getState().serverUrl;
    const url = `${baseUrl}/calendar/${selectedProfileId}/downloadspreadsheet`;
    Linking.openURL(url);
  };

  const accountName = (id: number | null) =>
    id != null ? (accounts.find((a) => a.id === id)?.name ?? 'Unknown') : 'Select account';

  // ── Render: single column page ────────────────────────────────────────────────
  const renderIncomeItem = (item: ExtrapolationItem) => {
    const isPaid = item.ledger_entry_id !== null;
    const isIncome = isIncomeItem(item);
    const isOverdue =
      !isPaid &&
      item.income_date != null &&
      item.income_date.slice(0, 10) < todayStr();
    return (
      <List.Item
        key={item.id}
        title={getItemName(item)}
        titleStyle={isPaid ? styles.paidText : undefined}
        style={[
          isPaid ? styles.paidItem : undefined,
          isOverdue && styles.overdueItem,
        ]}
        onPress={() => handleItemTap(item)}
        onLongPress={() => handleLongPressPaid(item)}
        disabled={longPressMarkingId === item.id}
        left={() => (
          <List.Icon
            icon={isPaid ? 'check-circle' : isIncome ? 'cash' : 'circle-outline'}
            color={isPaid ? '#66bb6a' : isOverdue ? theme.colors.error : isIncome ? theme.colors.primary : theme.colors.onSurfaceVariant}
          />
        )}
        right={() => (
          <Text
            style={[
              styles.itemAmount,
              isIncome ? { color: theme.colors.primary } : styles.expenseAmount,
              isPaid && styles.paidText,
              isOverdue && { color: theme.colors.error },
            ]}
          >
            {isIncome ? '+' : '-'}${Math.abs(item.amount).toFixed(2)}
          </Text>
        )}
      />
    );
  };

  const renderColumn = ({ item: col }: { item: IncomeColumn }) => {
    const colIncomeItems = col.items.filter(isIncomeItem);
    const colExpenseItems = col.items.filter((i) => !isIncomeItem(i));
    const net = col.incomeTotal - col.expenseTotal;

    return (
      <View style={[styles.column, { width: COLUMN_WIDTH }]}>
        <ScrollView showsVerticalScrollIndicator={false}>
          {colIncomeItems.map(renderIncomeItem)}
          {colIncomeItems.length > 0 && colExpenseItems.length > 0 && (
            <Divider style={[styles.columnInternalDivider, { backgroundColor: theme.colors.surface }]} />
          )}
          {colExpenseItems.map(renderIncomeItem)}

          <View style={[styles.columnFooter, { backgroundColor: theme.colors.surfaceVariant }]}>
            {col.carryForward !== 0 && (
              <View style={styles.columnFooterRow}>
                <Text style={[styles.columnFooterLabel, { color: theme.colors.onSurfaceVariant }]}>Carried forward</Text>
                <Text style={[col.carryForward >= 0 ? styles.positiveNet : { color: theme.colors.error }, styles.columnFooterValue]}>
                  {col.carryForward >= 0 ? '+' : '-'}${Math.abs(col.carryForward).toFixed(2)}
                </Text>
              </View>
            )}
            <View style={styles.columnFooterRow}>
              <Text style={[styles.columnFooterLabel, { color: theme.colors.onSurfaceVariant }]}>In</Text>
              <Text style={[{ color: theme.colors.primary }, styles.columnFooterValue]}>+${col.incomeTotal.toFixed(2)}</Text>
            </View>
            <View style={styles.columnFooterRow}>
              <Text style={[styles.columnFooterLabel, { color: theme.colors.onSurfaceVariant }]}>Out</Text>
              <Text style={[styles.expenseAmount, styles.columnFooterValue]}>-${col.expenseTotal.toFixed(2)}</Text>
            </View>
            <Divider style={[styles.footerDivider, { backgroundColor: theme.colors.surface }]} />
            <View style={styles.columnFooterRow}>
              <Text style={[styles.columnFooterLabel, { color: theme.colors.onSurfaceVariant }]}>Balance</Text>
              <Text style={[styles.columnFooterNet, (col.carryForward + net) >= 0 ? styles.positiveNet : { color: theme.colors.error }]}>
                {(col.carryForward + net) >= 0 ? '+' : '-'}${Math.abs(col.carryForward + net).toFixed(2)}
              </Text>
            </View>
            <View style={styles.columnFooterRow}>
              <Text style={[styles.columnFooterLabel, { color: theme.colors.onSurfaceVariant }]}>Safe to Spend</Text>
              <Text style={[styles.columnFooterNet, { color: net >= 0 ? '#4caf50' : theme.colors.error, fontWeight: 'bold' }]}>
                {net >= 0 ? '+' : '-'}${Math.abs(net).toFixed(2)}
              </Text>
            </View>
          </View>
        </ScrollView>
      </View>
    );
  };

  // ── Render: schedule tab ──────────────────────────────────────────────────────
  const renderScheduleTab = () => (
    <View style={styles.flex}>
      {unscheduledItems.length > 0 && (
        <View style={styles.warningBanner}>
          <Text style={[styles.warningText, { color: theme.colors.background }]}>
            {unscheduledItems.length} item{unscheduledItems.length !== 1 ? 's' : ''} without a scheduled date
          </Text>
          <Button mode="text" compact textColor={theme.colors.background} onPress={openFixDialog} style={styles.warningButton}>
            Fix
          </Button>
        </View>
      )}

      {incomeColumns.length === 0 ? (
        <Text variant="bodyMedium" style={styles.emptyText}>
          No scheduled items — run extrapolation to populate the calendar
        </Text>
      ) : (
        <>
          {/* Column navigation header */}
          <View style={styles.columnNav}>
            <IconButton
              icon="chevron-left"
              size={22}
              disabled={columnIndex === 0}
              onPress={goToPrevColumn}
              style={styles.navButton}
            />
            <View style={styles.columnNavCenter}>
              <View style={styles.columnNavDateRow}>
                <Text style={[styles.columnNavDate, { color: theme.colors.primary }]}>
                  {formatDateHeader(incomeColumns[columnIndex]?.date ?? '')}
                </Text>
                {columnIndex === currentPeriodIndex && (
                  <Badge style={[styles.todayBadge, { backgroundColor: theme.colors.primary }]} size={20}>
                    Today
                  </Badge>
                )}
              </View>
              <Text style={[styles.columnNavPager, { color: theme.colors.onSurfaceVariant }]}>
                {columnIndex + 1} / {incomeColumns.length}
              </Text>
            </View>
            <IconButton
              icon="refresh"
              size={18}
              onPress={() => fetchData(true)}
              disabled={refreshing}
              style={styles.navButton}
            />
            <IconButton
              icon="chevron-right"
              size={22}
              disabled={columnIndex === incomeColumns.length - 1}
              onPress={goToNextColumn}
              style={styles.navButton}
            />
          </View>

          <FlatList
            ref={flatListRef}
            data={incomeColumns}
            keyExtractor={(col) => col.date}
            horizontal
            showsHorizontalScrollIndicator={false}
            pagingEnabled
            snapToInterval={COLUMN_WIDTH}
            decelerationRate="fast"
            onMomentumScrollEnd={(e) => {
              const newIdx = Math.round(e.nativeEvent.contentOffset.x / COLUMN_WIDTH);
              setColumnIndex(newIdx);
            }}
            renderItem={renderColumn}
            getItemLayout={(_, index) => ({
              length: COLUMN_WIDTH,
              offset: COLUMN_WIDTH * index,
              index,
            })}
            style={styles.flex}
          />
        </>
      )}
    </View>
  );

  // ── Render: actions tab ────────────────────────────────────────────────────────
  const renderActionsTab = () => (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView keyboardShouldPersistTaps="handled">
        {/* Got Paid */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>I Got Paid</Text>
        <Text variant="bodySmall" style={styles.sectionHint}>
          {unpaidIncomeItems.length > 0
            ? `${unpaidIncomeItems.length} unpaid income item${unpaidIncomeItems.length !== 1 ? 's' : ''} — mark as received.`
            : 'No unpaid income items.'}
        </Text>
        <Button
          mode="contained"
          onPress={openGotPaid}
          disabled={unpaidIncomeItems.length === 0}
          style={[styles.actionButton, { backgroundColor: '#66bb6a' }]}
        >
          I Got Paid
        </Button>

        <Divider style={[styles.sectionDivider, { backgroundColor: theme.colors.surface }]} />

        {/* Add One-Off Item */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>Add One-Off Item</Text>

        <TextInput label="Name" value={oneOffName} onChangeText={setOneOffName} mode="outlined" style={styles.input} />
        <TextInput
          label="Amount"
          value={oneOffAmount}
          onChangeText={setOneOffAmount}
          mode="outlined"
          keyboardType="decimal-pad"
          style={styles.input}
        />
        <SegmentedButtons
          value={oneOffType}
          onValueChange={(v) => setOneOffType(v as 'expense' | 'income')}
          buttons={[{ value: 'expense', label: 'Expense' }, { value: 'income', label: 'Income' }]}
          style={styles.segmented}
        />
        <TextInput
          label="Date (YYYY-MM-DD)"
          value={oneOffDate}
          onChangeText={setOneOffDate}
          mode="outlined"
          style={styles.input}
        />
        <Button
          mode="outlined"
          onPress={() => setOneOffAccountPickerVisible(true)}
          style={[styles.pickerButton, { borderColor: theme.colors.primary }]}
          contentStyle={styles.pickerButtonContent}
        >
          Account: {accountName(oneOffAccountId)}
        </Button>
        <View style={styles.switchRow}>
          <Text variant="bodyMedium">Already paid</Text>
          <Switch value={oneOffPaid} onValueChange={setOneOffPaid} color={theme.colors.primary} />
        </View>
        <Button mode="contained" onPress={handleAddOneOff} loading={savingOneOff} disabled={savingOneOff} style={styles.actionButton}>
          Add Item
        </Button>

        <Divider style={[styles.sectionDivider, { backgroundColor: theme.colors.surface }]} />

        {/* Compute Savings */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>Compute Savings</Text>
        <Button
          mode="outlined"
          onPress={() => setSavingsAccountPickerVisible(true)}
          style={[styles.pickerButton, { borderColor: theme.colors.primary }]}
          contentStyle={styles.pickerButtonContent}
        >
          Savings account: {accountName(savingsAccountId)}
        </Button>
        <TextInput
          label="Spending buffer"
          value={spendingBuffer}
          onChangeText={setSpendingBuffer}
          mode="outlined"
          keyboardType="decimal-pad"
          style={styles.input}
        />
        <Button
          mode="contained"
          onPress={handleComputeSavings}
          loading={computing}
          disabled={computing || savingsAccountId == null}
          style={styles.actionButton}
        >
          Compute
        </Button>

        <Divider style={[styles.sectionDivider, { backgroundColor: theme.colors.surface }]} />

        {/* Run Extrapolation */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>Run Extrapolation</Text>
        <Text variant="bodySmall" style={styles.sectionHint}>
          Schedules all budget items into the calendar based on their periods and income dates.
        </Text>
        <Button
          mode="contained"
          onPress={() => setExtrapolateDialogVisible(true)}
          style={[styles.actionButton, styles.extrapolateButton, { backgroundColor: theme.colors.primary }]}
        >
          Run Extrapolation
        </Button>

        <Divider style={[styles.sectionDivider, { backgroundColor: theme.colors.surface }]} />

        {/* Export */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>Export</Text>
        <Button
          mode="contained"
          onPress={handleDownloadSpreadsheet}
          style={styles.actionButton}
        >
          Download Spreadsheet
        </Button>

        <Divider style={[styles.sectionDivider, { backgroundColor: theme.colors.surface }]} />

        {/* AI Analysis */}
        <Text variant="titleMedium" style={[styles.sectionTitle, { color: theme.colors.primary }]}>AI Analysis</Text>
        <Text variant="bodySmall" style={styles.sectionHint}>
          Get AI-powered insights and suggestions for your budget.
        </Text>
        <Button
          mode="contained"
          onPress={handleAiAnalysis}
          loading={aiLoading}
          style={styles.actionButton}
        >
          Analyze Budget
        </Button>

        <View style={styles.bottomPad} />
      </ScrollView>
    </KeyboardAvoidingView>
  );

  // ── Main render ───────────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Text variant="titleLarge" style={styles.title}>Calendar</Text>

        {!selectedProfileId ? (
          <Text variant="bodyMedium" style={styles.emptyText}>Select a profile in Settings to view calendar</Text>
        ) : loading && !refreshing ? (
          <ActivityIndicator animating color={theme.colors.primary} style={styles.loader} />
        ) : error ? (
          <View>
            <Text variant="bodySmall" style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
            <Button mode="outlined" onPress={() => fetchData()} style={styles.retryButton}>Retry</Button>
          </View>
        ) : (
          <View style={styles.flex}>
            <SegmentedButtons
              value={activeTab}
              onValueChange={(v) => setActiveTab(v as 'schedule' | 'actions')}
              buttons={[{ value: 'schedule', label: 'Schedule' }, { value: 'actions', label: 'Actions' }]}
              style={styles.tabs}
            />
            {activeTab === 'schedule' ? renderScheduleTab() : renderActionsTab()}
          </View>
        )}
      </View>

      {/* ── Dialogs ── */}
      <Portal>
        {/* Item detail dialog */}
        <Dialog visible={itemDetailVisible} onDismiss={() => setItemDetailVisible(false)}>
          <Dialog.Title>{selectedItem ? getItemName(selectedItem) : ''}</Dialog.Title>
          <Dialog.Content>
            <View style={styles.detailRow}>
              <Text variant="bodySmall" style={[styles.detailLabel, { color: theme.colors.onSurfaceVariant }]}>Amount</Text>
              <Text
                variant="bodyLarge"
                style={selectedItem && isIncomeItem(selectedItem) ? { color: theme.colors.primary } : styles.expenseAmount}
              >
                {selectedItem && isIncomeItem(selectedItem) ? '+' : '-'}${selectedItem ? Math.abs(selectedItem.amount).toFixed(2) : ''}
              </Text>
            </View>
            <View style={styles.detailRow}>
              <Text variant="bodySmall" style={[styles.detailLabel, { color: theme.colors.onSurfaceVariant }]}>Date</Text>
              <Text variant="bodyMedium">{selectedItem?.income_date?.slice(0, 10)}</Text>
            </View>
            <View style={styles.detailRow}>
              <Text variant="bodySmall" style={[styles.detailLabel, { color: theme.colors.onSurfaceVariant }]}>Status</Text>
              <Text variant="bodyMedium" style={selectedItem?.ledger_entry_id ? styles.paidStatus : undefined}>
                {selectedItem?.ledger_entry_id ? 'Paid' : 'Unpaid'}
              </Text>
            </View>

            {selectedItem && !selectedItem.ledger_entry_id && (
              <>
                <Divider style={[styles.detailDivider, { backgroundColor: theme.colors.surface }]} />
                <Text variant="labelMedium" style={[styles.detailLabel, { color: theme.colors.onSurfaceVariant }]}>
                  {isIncomeItem(selectedItem) ? 'Mark received — account' : 'Mark paid — account'}
                </Text>
                <RadioButton.Group
                  value={itemAccountId != null ? String(itemAccountId) : ''}
                  onValueChange={(v) => setItemAccountId(Number(v))}
                >
                  {accounts.map((a) => (
                    <RadioButton.Item key={a.id} label={a.name} value={String(a.id)} />
                  ))}
                </RadioButton.Group>
              </>
            )}
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setItemDetailVisible(false)}>Close</Button>
            {selectedItem && !selectedItem.ledger_entry_id && selectedItem.budget_item_id != null && selectedItem.income_date && (
              <>
                <Button onPress={() => openMoveDialog(selectedItem)}>Move</Button>
                <Button onPress={() => openSplitDialog(selectedItem)}>Split</Button>
              </>
            )}
            {selectedItem && !selectedItem.ledger_entry_id && (
              <Button
                onPress={handleMarkItemReceived}
                loading={markingItemPaid}
                disabled={markingItemPaid || itemAccountId == null}
              >
                {isIncomeItem(selectedItem) ? 'Mark Received' : 'Mark Paid'}
              </Button>
            )}
          </Dialog.Actions>
        </Dialog>

        {/* Move item dialog */}
        <Dialog visible={moveDialogVisible} onDismiss={() => { setMoveDialogVisible(false); setMoveItem(null); }}>
          <Dialog.Title>Move {moveItem?.name}</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 4 }}>
              Amount: ${moveItem?.amount?.toFixed(2)}
            </Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
              From {moveItem?.from_income_date ? formatDateHeader(moveItem.from_income_date) : ''} — choose destination:
            </Text>
          </Dialog.Content>
          <Dialog.ScrollArea style={{ maxHeight: 300 }}>
            <ScrollView>
              {incomeColumns
                .filter((col) => col.date !== moveItem?.from_income_date)
                .map((col) => {
                  const endingBalance = col.carryForward + col.incomeTotal - col.expenseTotal;
                  const afterMove = endingBalance - (moveItem?.amount ?? 0);
                  const goesNegative = afterMove < 0;
                  return (
                    <List.Item
                      key={col.date}
                      title={formatDateHeader(col.date)}
                      description={`Balance: $${endingBalance.toFixed(2)} → $${afterMove.toFixed(2)}${goesNegative ? '  ⚠ goes negative' : ''}`}
                      descriptionStyle={goesNegative ? { color: '#ef5350' } : undefined}
                      onPress={() => handleMoveItem(col.date)}
                      disabled={movingItem}
                      left={() => <List.Icon icon="calendar" color={goesNegative ? '#ef5350' : theme.colors.primary} />}
                    />
                  );
                })}
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => { setMoveDialogVisible(false); setMoveItem(null); }}>Cancel</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Split item dialog */}
        <Dialog visible={splitDialogVisible} onDismiss={() => { setSplitDialogVisible(false); setSplitItem(null); }}>
          <Dialog.Title>Split {splitItem ? getItemName(splitItem) : ''}</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
              Total amount: ${splitItem ? Math.abs(splitItem.amount).toFixed(2) : '0.00'}
            </Text>
            <TextInput
              label="Amount to keep"
              value={splitKeepAmount}
              onChangeText={setSplitKeepAmount}
              mode="outlined"
              keyboardType="decimal-pad"
              style={styles.dialogInput}
            />
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 12 }}>
              Remainder: ${splitItem && splitKeepAmount ? Math.max(0, Math.abs(splitItem.amount) - (parseFloat(splitKeepAmount) || 0)).toFixed(2) : '0.00'}
            </Text>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 6 }}>
              Move remainder to column:
            </Text>
          </Dialog.Content>
          <Dialog.ScrollArea style={{ maxHeight: 200 }}>
            <ScrollView>
              <RadioButton.Group value={splitDestDate} onValueChange={setSplitDestDate}>
                {incomeColumns
                  .filter((col) => col.date !== splitItem?.income_date?.slice(0, 10))
                  .map((col) => (
                    <RadioButton.Item
                      key={col.date}
                      label={`${formatDateHeader(col.date)}  (bal $${(col.carryForward + col.incomeTotal - col.expenseTotal).toFixed(2)})`}
                      value={col.date}
                    />
                  ))}
              </RadioButton.Group>
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => { setSplitDialogVisible(false); setSplitItem(null); }}>Cancel</Button>
            <Button
              onPress={handleSplitItem}
              loading={splittingItem}
              disabled={splittingItem || !splitDestDate || !splitKeepAmount}
            >
              Split
            </Button>
          </Dialog.Actions>
        </Dialog>

        {/* Got Paid dialog */}
        <Dialog visible={gotPaidVisible} onDismiss={() => setGotPaidVisible(false)}>
          <Dialog.Title>I Got Paid</Dialog.Title>
          <Dialog.Content>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 6 }}>Income item</Text>
            <RadioButton.Group
              value={gotPaidItemId != null ? String(gotPaidItemId) : ''}
              onValueChange={(v) => setGotPaidItemId(Number(v))}
            >
              {unpaidIncomeItems.map((item) => (
                <RadioButton.Item
                  key={item.id}
                  label={`${getItemName(item)} — ${item.income_date?.slice(0, 10)} ($${item.amount.toFixed(2)})`}
                  value={String(item.id)}
                />
              ))}
            </RadioButton.Group>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 12, marginBottom: 6 }}>Account</Text>
            <RadioButton.Group
              value={gotPaidAccountId != null ? String(gotPaidAccountId) : ''}
              onValueChange={(v) => setGotPaidAccountId(Number(v))}
            >
              {accounts.map((a) => (
                <RadioButton.Item key={a.id} label={a.name} value={String(a.id)} />
              ))}
            </RadioButton.Group>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setGotPaidVisible(false)}>Cancel</Button>
            <Button
              onPress={handleGotPaid}
              loading={markingPaid}
              disabled={markingPaid || gotPaidItemId == null || gotPaidAccountId == null}
            >
              Mark Received
            </Button>
          </Dialog.Actions>
        </Dialog>

        {/* One-off account picker */}
        <Dialog visible={oneOffAccountPickerVisible} onDismiss={() => setOneOffAccountPickerVisible(false)}>
          <Dialog.Title>Select Account</Dialog.Title>
          <Dialog.Content>
            <RadioButton.Group
              value={oneOffAccountId != null ? String(oneOffAccountId) : ''}
              onValueChange={(v) => setOneOffAccountId(v ? Number(v) : null)}
            >
              <RadioButton.Item label="None" value="" />
              {accounts.map((a) => (
                <RadioButton.Item key={a.id} label={a.name} value={String(a.id)} />
              ))}
            </RadioButton.Group>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setOneOffAccountPickerVisible(false)}>Done</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Savings account picker */}
        <Dialog visible={savingsAccountPickerVisible} onDismiss={() => setSavingsAccountPickerVisible(false)}>
          <Dialog.Title>Select Savings Account</Dialog.Title>
          <Dialog.Content>
            <RadioButton.Group
              value={savingsAccountId != null ? String(savingsAccountId) : ''}
              onValueChange={(v) => setSavingsAccountId(v ? Number(v) : null)}
            >
              {accounts.map((a) => (
                <RadioButton.Item key={a.id} label={a.name} value={String(a.id)} />
              ))}
            </RadioButton.Group>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setSavingsAccountPickerVisible(false)}>Done</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Compute savings confirm */}
        <Dialog visible={computeConfirmVisible} onDismiss={() => setComputeConfirmVisible(false)}>
          <Dialog.Title>Save Computed Savings?</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium" style={{ marginBottom: 8 }}>
              {computedEntries?.length ?? 0} savings entries found:
            </Text>
            <Dialog.ScrollArea style={styles.computedScrollArea}>
              <ScrollView>
                {computedEntries?.map((entry, i) => (
                  <View key={i} style={styles.computedRow}>
                    <Text style={styles.computedDate}>{entry.date}</Text>
                    <Text style={styles.computedAmount}>${entry.amount.toFixed(2)}</Text>
                  </View>
                ))}
              </ScrollView>
            </Dialog.ScrollArea>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setComputeConfirmVisible(false)}>Cancel</Button>
            <Button onPress={handleSaveComputedSavings} loading={savingComputed} disabled={savingComputed}>Save</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Extrapolation confirm */}
        <Dialog visible={extrapolateDialogVisible} onDismiss={() => setExtrapolateDialogVisible(false)}>
          <Dialog.Title>Run Budget Extrapolation?</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium" style={styles.dialogDescription}>
              Extrapolation schedules your recurring budget items across the date range you've selected. Here's how it works:
            </Text>
            <Text variant="bodySmall" style={styles.dialogDescription}>
              {'\u2022'} Your income items become columns in the schedule — one column per payday{'\n'}
              {'\u2022'} Expenses are placed into the earliest column that can cover them{'\n'}
              {'\u2022'} If an expense can't fit anywhere, it's marked as unscheduled for you to handle manually{'\n'}
              {'\u2022'} Items you've already marked as paid are preserved
            </Text>
            <Text variant="bodySmall" style={styles.dialogDescription}>
              After extrapolation, take a moment to review the results. The scheduling algorithm does its best, but you know your finances better than any algorithm.
            </Text>
            <Text variant="bodySmall" style={styles.dialogDescription}>
              Once your schedule looks right, consider adding savings items to start building a safety net — even small amounts add up.
            </Text>
            <Text variant="bodySmall" style={[styles.dialogDescription, { marginBottom: 20 }]}>
              You've got this!
            </Text>
            <TextInput
              label="Start date (YYYY-MM-DD)"
              value={extrapolateStart}
              onChangeText={setExtrapolateStart}
              mode="outlined"
              style={styles.dialogInput}
            />
            <TextInput
              label="End date (YYYY-MM-DD)"
              value={extrapolateEnd}
              onChangeText={setExtrapolateEnd}
              mode="outlined"
              style={styles.dialogInput}
            />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setExtrapolateDialogVisible(false)}>Cancel</Button>
            <Button onPress={handleRunExtrapolation} loading={extrapolating} disabled={extrapolating}>Run</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Fix unscheduled */}
        <Dialog visible={fixDialogVisible} onDismiss={() => setFixDialogVisible(false)}>
          <Dialog.Title>Schedule Unscheduled Items</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodySmall" style={{ marginBottom: 8 }}>Assign a date to each unscheduled item:</Text>
            <Dialog.ScrollArea style={styles.fixScrollArea}>
              <ScrollView>
                {unscheduledItems.map((item) => (
                  <View key={item.id} style={styles.fixRow}>
                    <Text style={styles.fixItemName}>{getItemName(item)}</Text>
                    <TextInput
                      value={unscheduledDates[item.id] ?? ''}
                      onChangeText={(v) => setUnscheduledDates((prev) => ({ ...prev, [item.id]: v }))}
                      mode="outlined"
                      placeholder="YYYY-MM-DD"
                      style={styles.fixDateInput}
                      dense
                    />
                  </View>
                ))}
              </ScrollView>
            </Dialog.ScrollArea>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setFixDialogVisible(false)}>Cancel</Button>
            <Button onPress={handleFixUnscheduled} loading={fixing} disabled={fixing || !fixAllDatesSelected}>Save</Button>
          </Dialog.Actions>
        </Dialog>

        {/* AI Analysis */}
        <Dialog visible={aiAnalysisVisible} onDismiss={() => setAiAnalysisVisible(false)} style={{ maxHeight: '80%' }}>
          <Dialog.Title>AI Budget Analysis</Dialog.Title>
          <Dialog.ScrollArea>
            <ScrollView style={{ paddingHorizontal: 20 }}>
              {aiLoading && (
                <View style={{ alignItems: 'center', padding: 40 }}>
                  <ActivityIndicator size="large" />
                  <Text style={{ marginTop: 16 }}>Analyzing your budget...</Text>
                </View>
              )}
              {aiError && <Text style={{ color: theme.colors.error }}>{aiError}</Text>}
              {aiAnalysis && <SimpleMarkdown text={aiAnalysis} />}
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setAiAnalysisVisible(false)}>Close</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={2500}>
        {snackbar}
      </Snackbar>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  flex: { flex: 1 },
  title: { marginBottom: 12 },
  loader: { marginTop: 32 },
  errorText: { marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  emptyText: { opacity: 0.7, marginTop: 16 },

  tabs: { marginBottom: 8 },

  // Warning banner
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFC107',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginBottom: 8,
  },
  warningText: { flex: 1, fontSize: 13 },
  warningButton: { marginLeft: 8 },

  // Column pager nav
  columnNav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  navButton: { margin: 0 },
  columnNavCenter: { flex: 1, alignItems: 'center' },
  columnNavDateRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  columnNavDate: { fontWeight: '600', fontSize: 15 },
  columnNavPager: { fontSize: 11, marginTop: 1 },
  todayBadge: { fontSize: 10, fontWeight: '600', paddingHorizontal: 4 },

  // Column page
  column: { flex: 1 },
  columnInternalDivider: { marginVertical: 6 },
  columnFooter: {
    marginTop: 12,
    marginHorizontal: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: undefined,
    borderRadius: 8,
    marginBottom: 16,
  },
  columnFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
  },
  columnFooterLabel: { fontSize: 13 },
  columnFooterValue: { fontSize: 13, fontVariant: ['tabular-nums'] },
  footerDivider: { marginVertical: 6 },
  columnFooterNet: { fontSize: 15, fontWeight: '700', fontVariant: ['tabular-nums'] },
  positiveNet: { color: '#66bb6a' },
  negativeNet: {},

  // List items
  overdueItem: {
    borderLeftWidth: 3,
    borderLeftColor: '#ef5350',
    backgroundColor: 'rgba(239, 83, 80, 0.08)',
  },
  paidItem: { opacity: 0.45 },
  paidText: { opacity: 0.5 },
  paidStatus: { color: '#66bb6a' },
  itemAmount: {
    alignSelf: 'center',
    fontSize: 15,
    fontVariant: ['tabular-nums'],
    marginRight: 8,
  },
  incomeAmount: {},
  expenseAmount: { color: '#e0e0e0' },

  // Actions tab
  sectionTitle: { marginBottom: 12, marginTop: 8 },
  sectionHint: { opacity: 0.6, marginBottom: 12 },
  sectionDivider: { marginVertical: 20 },
  input: { marginBottom: 12 },
  segmented: { marginBottom: 12 },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  pickerButton: { marginBottom: 12 },
  pickerButtonContent: { justifyContent: 'flex-start' },
  actionButton: { marginBottom: 4 },
  extrapolateButton: {},
  bottomPad: { height: 40 },

  // Dialogs
  dialogDescription: { marginBottom: 16, opacity: 0.8 },
  dialogInput: { marginBottom: 12 },
  computedScrollArea: { maxHeight: 200 },
  computedRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  computedDate: { fontSize: 13, color: '#ccc' },
  computedAmount: { fontSize: 13, fontVariant: ['tabular-nums'], color: '#ccc' },
  fixScrollArea: { maxHeight: 300 },
  fixRow: { marginBottom: 10 },
  fixItemName: { fontSize: 13, color: '#ccc', marginBottom: 4 },
  fixDateInput: { height: 40 },

  // Item detail dialog
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailLabel: {},
  detailDivider: { marginVertical: 12 },
});
