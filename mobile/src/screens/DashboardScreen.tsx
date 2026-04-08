import React, { useState, useCallback } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import {
  Text,
  ActivityIndicator,
  Button,
  Dialog,
  Portal,
  Snackbar,
  RadioButton,
  List,
  TextInput,
  Badge,
  useTheme,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useStore, Account } from '../store/store';
import { api } from '../api/api';

interface DashboardItem {
  id: number;
  name: string;
  type: string;
  amount: number;
  due_date: string;
  income_date: string | null;
  budget_item_id: number | null;
  is_paid: boolean;
  category: string | null;
}

interface DashboardColumn {
  income_date: string;
  income: number;
  expenses: number;
  paid_expenses: number;
  starting_balance: number;
  safe_to_spend: number;
  ending_balance: number;
}

interface DashboardData {
  upcoming: DashboardItem[];
  overdue: DashboardItem[];
  current_column: DashboardColumn | null;
  columns: DashboardColumn[];
  total_unpaid: number;
  total_paid: number;
  account_count: number;
  budget_item_count: number;
}

interface ProfileResponse {
  id: number;
  name: string;
  accounts: Account[];
  budget_items: unknown[];
  budget_groups: unknown[];
}

export default function DashboardScreen() {
  const { selectedProfileId } = useStore();
  const theme = useTheme();

  const [data, setData] = useState<DashboardData | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mark-paid dialog state
  const [dialogVisible, setDialogVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<DashboardItem | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [paying, setPaying] = useState(false);

  // Quick add expense state
  const [expenseName, setExpenseName] = useState('');
  const [expenseAmount, setExpenseAmount] = useState('');
  const [saving, setSaving] = useState(false);

  const [snackbar, setSnackbar] = useState('');

  const fetchData = useCallback(async (isRefresh = false) => {
    if (!selectedProfileId) return;
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const [dashboard, profile] = await Promise.all([
        api.get<DashboardData>(`/dashboard/${selectedProfileId}`),
        api.get<ProfileResponse>(`/profiles/${selectedProfileId}`),
      ]);
      setData(dashboard);
      setAccounts(profile.accounts);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load dashboard');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedProfileId]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  const openPayDialog = (item: DashboardItem) => {
    setSelectedItem(item);
    setSelectedAccountId(null);
    setDialogVisible(true);
  };

  const handleConfirmPay = async () => {
    if (!selectedItem || !selectedAccountId || !selectedProfileId) return;
    setPaying(true);
    try {
      await api.post(`/budget/markpaid/${selectedProfileId}`, {
        extrapolationItemId: selectedItem.id,
        accountId: selectedAccountId,
      });
      setDialogVisible(false);
      setSelectedItem(null);
      setSnackbar('Marked as paid');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to mark as paid');
    } finally {
      setPaying(false);
    }
  };

  const handleQuickAdd = async () => {
    if (!selectedProfileId || !expenseName.trim() || !expenseAmount.trim()) return;
    const amount = parseFloat(expenseAmount);
    if (isNaN(amount)) {
      setSnackbar('Invalid amount');
      return;
    }
    setSaving(true);
    try {
      await api.post(`/calendar/${selectedProfileId}/oneoff`, {
        name: expenseName.trim(),
        amount,
      });
      setExpenseName('');
      setExpenseAmount('');
      setSnackbar('Expense added');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to add expense');
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  const daysAway = (dateStr: string) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(dateStr + 'T00:00:00');
    const diff = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (diff === 0) return 'Today';
    if (diff === 1) return 'Tomorrow';
    return `${diff} days`;
  };

  const todayStr = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const greenColor = '#66bb6a';
  const redColor = '#ef5350';

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Header */}
        <Text variant="titleLarge" style={styles.headerTitle}>Dashboard</Text>
        <Text variant="bodySmall" style={{ opacity: 0.6, marginBottom: 16 }}>{todayStr}</Text>

        {!selectedProfileId ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            Select a profile in Settings to view your dashboard
          </Text>
        ) : loading && !refreshing ? (
          <ActivityIndicator animating={true} color={theme.colors.primary} style={styles.loader} />
        ) : error ? (
          <View>
            <Text variant="bodySmall" style={{ color: theme.colors.error }}>{error}</Text>
            <Button mode="outlined" onPress={() => fetchData()} style={{ marginTop: 8 }}>
              Retry
            </Button>
          </View>
        ) : data ? (
          <ScrollView
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchData(true)}
                colors={[theme.colors.primary]}
              />
            }
            showsVerticalScrollIndicator={false}
          >
            {/* Safe to Spend Hero */}
            {data.current_column && (
              <View style={[
                styles.heroCard,
                {
                  borderLeftColor: data.current_column.safe_to_spend >= 0 ? greenColor : redColor,
                  backgroundColor: theme.colors.surface,
                },
              ]}>
                <Text
                  variant="headlineMedium"
                  style={{
                    color: data.current_column.safe_to_spend >= 0 ? greenColor : redColor,
                    fontWeight: 'bold',
                  }}
                >
                  ${Math.abs(data.current_column.safe_to_spend).toFixed(2)}
                  {data.current_column.safe_to_spend < 0 ? ' over' : ''}
                </Text>
                <Text variant="bodyMedium" style={{ opacity: 0.7, marginTop: 4 }}>
                  Safe to spend this period
                </Text>
                <View style={styles.heroDetails}>
                  <Text variant="bodySmall" style={{ opacity: 0.5 }}>
                    Period: {formatDate(data.current_column.income_date)}
                  </Text>
                  <Text variant="bodySmall" style={{ opacity: 0.5 }}>
                    Ending: ${data.current_column.ending_balance.toFixed(2)}
                  </Text>
                </View>
              </View>
            )}

            {/* Overdue Items */}
            {data.overdue.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Text variant="titleMedium" style={{ color: redColor }}>Overdue</Text>
                  <Badge style={[styles.badge, { backgroundColor: redColor }]}>{data.overdue.length}</Badge>
                </View>
                {data.overdue.map((item) => (
                  <List.Item
                    key={item.id}
                    title={item.name}
                    description={`$${Math.abs(item.amount).toFixed(2)}  --  Due ${formatDate(item.due_date)}`}
                    titleStyle={{ color: redColor }}
                    left={(props) => <List.Icon {...props} icon="alert-circle" color={redColor} />}
                    right={() => (
                      <Button
                        mode="contained"
                        compact
                        buttonColor={redColor}
                        onPress={() => openPayDialog(item)}
                        style={styles.payButton}
                      >
                        Pay
                      </Button>
                    )}
                  />
                ))}
              </View>
            )}

            {/* Upcoming Items */}
            {data.upcoming.length > 0 && (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Text variant="titleMedium" style={{ color: theme.colors.primary }}>Due Soon</Text>
                  <Badge style={[styles.badge, { backgroundColor: theme.colors.primary }]}>{data.upcoming.length}</Badge>
                </View>
                {data.upcoming.map((item) => (
                  <List.Item
                    key={item.id}
                    title={item.name}
                    description={`$${Math.abs(item.amount).toFixed(2)}  --  ${formatDate(item.due_date)}  --  ${daysAway(item.due_date)}`}
                    left={(props) => <List.Icon {...props} icon="clock-outline" color={theme.colors.primary} />}
                    right={() => (
                      <Button
                        mode="outlined"
                        compact
                        onPress={() => openPayDialog(item)}
                        style={styles.payButton}
                      >
                        Pay
                      </Button>
                    )}
                  />
                ))}
              </View>
            )}

            {/* Quick Add Expense */}
            <View style={styles.section}>
              <Text variant="titleMedium" style={{ color: theme.colors.primary, marginBottom: 8 }}>
                Quick Add Expense
              </Text>
              <View style={styles.quickAddRow}>
                <TextInput
                  label="Name"
                  value={expenseName}
                  onChangeText={setExpenseName}
                  mode="outlined"
                  dense
                  style={styles.quickAddInput}
                />
                <TextInput
                  label="Amount"
                  value={expenseAmount}
                  onChangeText={setExpenseAmount}
                  mode="outlined"
                  dense
                  keyboardType="decimal-pad"
                  style={[styles.quickAddInput, { maxWidth: 100 }]}
                />
                <Button
                  mode="contained"
                  compact
                  onPress={handleQuickAdd}
                  loading={saving}
                  disabled={saving || !expenseName.trim() || !expenseAmount.trim()}
                  style={styles.quickAddButton}
                >
                  Save
                </Button>
              </View>
            </View>

            {/* Period Overview */}
            {data.columns.length > 0 && (
              <View style={styles.section}>
                <Text variant="titleMedium" style={{ color: theme.colors.primary, marginBottom: 8 }}>
                  Period Overview
                </Text>
                {data.columns.map((col) => {
                  const isCurrent = data.current_column?.income_date === col.income_date;
                  return (
                    <View
                      key={col.income_date}
                      style={[
                        styles.periodCard,
                        {
                          backgroundColor: theme.colors.surface,
                          borderLeftColor: col.safe_to_spend >= 0 ? greenColor : redColor,
                          opacity: isCurrent ? 1 : 0.75,
                        },
                      ]}
                    >
                      <View style={styles.periodRow}>
                        <Text variant="bodyMedium" style={{ fontWeight: isCurrent ? 'bold' : 'normal' }}>
                          {formatDate(col.income_date)}
                          {isCurrent ? '  (current)' : ''}
                        </Text>
                        <Text
                          variant="bodyMedium"
                          style={{
                            color: col.safe_to_spend >= 0 ? greenColor : redColor,
                            fontWeight: 'bold',
                            fontVariant: ['tabular-nums'],
                          }}
                        >
                          ${col.safe_to_spend.toFixed(2)}
                        </Text>
                      </View>
                    </View>
                  );
                })}
              </View>
            )}

            {/* Bottom spacer */}
            <View style={{ height: 32 }} />
          </ScrollView>
        ) : null}
      </View>

      {/* Mark Paid Dialog */}
      <Portal>
        <Dialog visible={dialogVisible} onDismiss={() => setDialogVisible(false)}>
          <Dialog.Title>Mark as Paid</Dialog.Title>
          <Dialog.Content>
            {selectedItem && (
              <Text variant="bodyMedium" style={{ marginBottom: 12 }}>
                {selectedItem.name} -- ${Math.abs(selectedItem.amount).toFixed(2)}
              </Text>
            )}
            <RadioButton.Group
              onValueChange={(val) => setSelectedAccountId(Number(val))}
              value={selectedAccountId !== null ? String(selectedAccountId) : ''}
            >
              {accounts.map((account) => (
                <RadioButton.Item
                  key={account.id}
                  label={account.name}
                  value={String(account.id)}
                />
              ))}
            </RadioButton.Group>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDialogVisible(false)}>Cancel</Button>
            <Button
              onPress={handleConfirmPay}
              disabled={!selectedAccountId || paying}
              loading={paying}
            >
              Confirm
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar
        visible={!!snackbar}
        onDismiss={() => setSnackbar('')}
        duration={2000}
      >
        {snackbar}
      </Snackbar>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  headerTitle: { marginBottom: 4 },
  loader: { marginTop: 32 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  heroCard: {
    borderLeftWidth: 4,
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  heroDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  section: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  badge: {
    marginLeft: 8,
    color: '#fff',
  },
  payButton: {
    alignSelf: 'center',
  },
  quickAddRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  quickAddInput: {
    flex: 1,
  },
  quickAddButton: {
    alignSelf: 'center',
  },
  periodCard: {
    borderLeftWidth: 3,
    borderRadius: 6,
    padding: 10,
    marginBottom: 6,
  },
  periodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});
