import React, { useState, useCallback } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, List, ActivityIndicator, Button, Dialog, Portal, Snackbar, RadioButton, FAB, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { BudgetStackParamList } from '../navigation/BudgetStack';
import { useStore, Account, BudgetItem, BudgetGroup, ExtrapolationItem } from '../store/store';
import { api } from '../api/api';
import HelpIcon from '../components/HelpIcon';

type Props = NativeStackScreenProps<BudgetStackParamList, 'BudgetList'>;

interface ScheduleResponse {
  extrapolation_items: ExtrapolationItem[];
  [key: string]: any;
}

interface ProfileResponse {
  id: number;
  name: string;
  accounts: Account[];
  budget_items: BudgetItem[];
  budget_groups: BudgetGroup[];
}

export default function BudgetScreen({ navigation }: Props) {
  const { selectedProfileId, setAccounts: storeSetAccounts } = useStore();
  const theme = useTheme();

  const [budgetItems, setBudgetItems] = useState<BudgetItem[]>([]);
  const [budgetGroups, setBudgetGroups] = useState<BudgetGroup[]>([]);
  const [extrapolationItems, setExtrapolationItems] = useState<ExtrapolationItem[]>([]);
  const [localAccounts, setLocalAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [dialogVisible, setDialogVisible] = useState(false);
  const [selectedItem, setSelectedItem] = useState<BudgetItem | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [paying, setPaying] = useState(false);
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
      const [profile, schedule] = await Promise.all([
        api.get<ProfileResponse>(`/profiles/${selectedProfileId}`),
        api.get<ScheduleResponse>(`/schedule/${selectedProfileId}`),
      ]);
      setBudgetItems(profile.budget_items);
      setBudgetGroups(profile.budget_groups);
      setExtrapolationItems(schedule.extrapolation_items);
      storeSetAccounts(profile.accounts);
      setLocalAccounts(profile.accounts);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load budget');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedProfileId, storeSetAccounts]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  const getItemStatus = (item: BudgetItem) => {
    const matching = extrapolationItems.filter(
      (ei) => ei.budget_item_id === item.id && ei.category === null
    );
    const isPayable = matching.length > 0;
    const isPaid = isPayable && matching.some((ei) => ei.ledger_entry_id !== null);
    const firstUnpaid = matching.find((ei) => ei.ledger_entry_id === null) ?? null;
    return { isPayable, isPaid, firstUnpaid };
  };

  const openMarkPaidDialog = (item: BudgetItem) => {
    setSelectedItem(item);
    setSelectedAccountId(null);
    setDialogVisible(true);
  };

  const handleConfirmPay = async () => {
    if (!selectedItem || !selectedAccountId || !selectedProfileId) return;
    const { firstUnpaid } = getItemStatus(selectedItem);
    if (!firstUnpaid) return;
    setPaying(true);
    try {
      await api.post(`/budget/markpaid/${selectedProfileId}`, {
        extrapolationItemId: firstUnpaid.id,
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

  const groupIds = new Set(budgetGroups.map((g) => g.id));
  const ungroupedItems = budgetItems.filter((item) => !groupIds.has(item.budget_group_id));

  const groupTotals = budgetGroups.map(group => ({
    id: group.id,
    name: group.name,
    total: budgetItems
      .filter(item => item.budget_group_id === group.id)
      .reduce((sum, item) => sum + item.amount, 0),
  })).filter(g => g.total > 0);

  const maxTotal = Math.max(...groupTotals.map(g => g.total), 1);

  const renderItem = (item: BudgetItem) => {
    const { isPayable, isPaid, firstUnpaid } = getItemStatus(item);
    return (
      <List.Item
        key={item.id}
        title={item.name}
        description={item.type}
        style={isPaid ? { opacity: 0.5 } : undefined}
        left={isPaid ? () => <List.Icon icon="check-circle" color="#66bb6a" /> : undefined}
        right={() => (
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={styles.amount}>${item.amount.toFixed(2)}</Text>
            <List.Icon icon="pencil" color="#555" />
          </View>
        )}
        onPress={
          isPayable && !isPaid && firstUnpaid
            ? () => openMarkPaidDialog(item)
            : () => navigation.navigate('BudgetItemForm', { groups: budgetGroups, item })
        }
        onLongPress={() => navigation.navigate('BudgetItemForm', { groups: budgetGroups, item })}
      />
    );
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
          <Text variant="titleLarge">Budget</Text>
          <HelpIcon text="Define recurring income and expenses with schedules. These get projected onto your calendar." />
        </View>

        {!selectedProfileId ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            Select a profile in Settings to view budget
          </Text>
        ) : loading && !refreshing ? (
          <ActivityIndicator animating={true} color={theme.colors.primary} style={styles.loader} />
        ) : error ? (
          <View>
            <Text variant="bodySmall" style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
            <Button mode="outlined" onPress={() => fetchData()} style={styles.retryButton}>
              Retry
            </Button>
          </View>
        ) : budgetItems.length === 0 && !loading ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No budget items yet.{'\n\n'}Budget items are your recurring income and expenses — rent, salary, subscriptions, etc. Each item has a schedule that tells Budgie when it occurs.{'\n\n'}Tap the + button to add your first one, then run Extrapolation from the Calendar to see it on your schedule.
          </Text>
        ) : (
          <ScrollView
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchData(true)}
                colors={[theme.colors.primary]}
              />
            }
          >
            {budgetGroups.map((group) => {
              const items = budgetItems.filter((item) => item.budget_group_id === group.id);
              return (
                <List.Section key={group.id} title={group.name} titleStyle={{ color: theme.colors.primary }}>
                  {items.map(renderItem)}
                </List.Section>
              );
            })}
            {ungroupedItems.length > 0 && (
              <List.Section title="Uncategorized" titleStyle={{ color: theme.colors.primary }}>
                {ungroupedItems.map(renderItem)}
              </List.Section>
            )}
            {budgetItems.length > 0 && groupTotals.length > 0 && (
              <View style={styles.chartSection}>
                <Text variant="titleMedium" style={[styles.chartTitle, { color: theme.colors.primary }]}>Budget Overview</Text>
                {groupTotals.map(group => (
                  <View key={group.id} style={styles.chartRow}>
                    <Text style={styles.chartLabel} numberOfLines={1}>{group.name}</Text>
                    <View style={[styles.chartTrack, { backgroundColor: theme.colors.surface }]}>
                      <View style={[
                        styles.chartBar,
                        { width: `${(group.total / maxTotal) * 100}%`, backgroundColor: theme.colors.primary }
                      ]} />
                    </View>
                    <Text style={styles.chartAmount}>${group.total.toFixed(0)}</Text>
                  </View>
                ))}
              </View>
            )}
          </ScrollView>
        )}
      </View>

      <Portal>
        <Dialog visible={dialogVisible} onDismiss={() => setDialogVisible(false)}>
          <Dialog.Title>Mark as Paid</Dialog.Title>
          <Dialog.Content>
            {selectedItem && (
              <Text variant="bodyMedium" style={{ marginBottom: 12 }}>{selectedItem.name}</Text>
            )}
            <RadioButton.Group
              onValueChange={(val) => setSelectedAccountId(Number(val))}
              value={selectedAccountId !== null ? String(selectedAccountId) : ''}
            >
              {localAccounts.map((account) => (
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

      {selectedProfileId && (
        <FAB
          icon="plus"
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          color={theme.colors.background}
          onPress={() =>
            navigation.navigate('BudgetItemForm', { groups: budgetGroups })
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  title: { marginBottom: 16 },
  loader: { marginTop: 32 },
  errorText: { marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  amount: { alignSelf: 'center', fontVariant: ['tabular-nums'], fontSize: 16, marginRight: 8 },
  sectionTitle: {},
  chartSection: {
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: undefined,
  },
  chartTitle: {
    marginBottom: 16,
  },
  chartRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  chartLabel: {
    width: 100,
    fontSize: 13,
    color: '#ccc',
  },
  chartTrack: {
    flex: 1,
    height: 16,
    borderRadius: 4,
    marginHorizontal: 8,
  },
  chartBar: {
    height: 16,
    borderRadius: 4,
    minWidth: 4,
  },
  chartAmount: {
    width: 72,
    textAlign: 'right',
    fontSize: 13,
    fontVariant: ['tabular-nums'],
    color: '#ccc',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});
