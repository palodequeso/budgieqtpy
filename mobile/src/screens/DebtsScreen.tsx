import React, { useState, useCallback } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, KeyboardAvoidingView, Platform } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Dialog,
  Portal,
  Snackbar,
  List,
  ActivityIndicator,
  FAB,
  IconButton,
  DataTable,
  useTheme,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useStore } from '../store/store';
import { api } from '../api/api';
import HelpIcon from '../components/HelpIcon';

interface Debt {
  id: number;
  name: string;
  total_amount: number;
  remaining_amount: number;
  min_payment: number;
  interest_rate: number;
  created_at: string | null;
  updated_at: string | null;
}

interface DebtPaymentEntry {
  debt_id: number;
  debt_name: string;
  amount: number;
  income_date: string;
}

const EMPTY_FORM = {
  name: '',
  total_amount: '',
  remaining_amount: '',
  min_payment: '',
  interest_rate: '',
};

export default function DebtsScreen() {
  const { selectedProfileId } = useStore();
  const theme = useTheme();

  const [debts, setDebts] = useState<Debt[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState('');

  // Add/Edit dialog
  const [formVisible, setFormVisible] = useState(false);
  const [editingDebt, setEditingDebt] = useState<Debt | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  // Delete dialog
  const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);
  const [deletingDebt, setDeletingDebt] = useState<Debt | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Compute payments dialog
  const [computeDialogVisible, setComputeDialogVisible] = useState(false);
  const [savingsMargin, setSavingsMargin] = useState('');
  const [computing, setComputing] = useState(false);
  const [computedPayments, setComputedPayments] = useState<DebtPaymentEntry[] | null>(null);
  const [savingPayments, setSavingPayments] = useState(false);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (!selectedProfileId) return;
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await api.get<Debt[]>(`/debts/${selectedProfileId}`);
      setDebts(data);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load debts');
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

  // ── Add/Edit form ────────────────────────────────────────────────────────

  const openAddDialog = () => {
    setEditingDebt(null);
    setForm(EMPTY_FORM);
    setFormVisible(true);
  };

  const openEditDialog = (debt: Debt) => {
    setEditingDebt(debt);
    setForm({
      name: debt.name,
      total_amount: String(debt.total_amount),
      remaining_amount: String(debt.remaining_amount),
      min_payment: String(debt.min_payment),
      interest_rate: String(debt.interest_rate),
    });
    setFormVisible(true);
  };

  const handleSave = async () => {
    if (!selectedProfileId) return;
    if (!form.name.trim()) { setSnackbar('Name is required'); return; }
    if (!form.total_amount || isNaN(parseFloat(form.total_amount))) {
      setSnackbar('Total amount must be a number'); return;
    }
    if (!form.remaining_amount || isNaN(parseFloat(form.remaining_amount))) {
      setSnackbar('Remaining amount must be a number'); return;
    }

    const body = {
      name: form.name.trim(),
      total_amount: parseFloat(form.total_amount),
      remaining_amount: parseFloat(form.remaining_amount),
      min_payment: parseFloat(form.min_payment) || 0,
      interest_rate: parseFloat(form.interest_rate) || 0,
    };

    setSaving(true);
    try {
      if (editingDebt) {
        await api.put(`/debts/${selectedProfileId}/${editingDebt.id}`, body);
        setSnackbar('Debt updated');
      } else {
        await api.post(`/debts/${selectedProfileId}`, body);
        setSnackbar('Debt added');
      }
      setFormVisible(false);
      setEditingDebt(null);
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save debt');
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ──────────────────────────────────────────────────────────────

  const openDeleteDialog = (debt: Debt) => {
    setDeletingDebt(debt);
    setDeleteDialogVisible(true);
  };

  const handleDelete = async () => {
    if (!selectedProfileId || !deletingDebt) return;
    setDeleting(true);
    try {
      await api.del(`/debts/${selectedProfileId}/${deletingDebt.id}`);
      setDeleteDialogVisible(false);
      setDeletingDebt(null);
      setSnackbar('Debt deleted');
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to delete debt');
    } finally {
      setDeleting(false);
    }
  };

  // ── Compute payments ────────────────────────────────────────────────────

  const openComputeDialog = () => {
    setSavingsMargin('');
    setComputedPayments(null);
    setComputeDialogVisible(true);
  };

  const handleCompute = async () => {
    if (!selectedProfileId) return;
    setComputing(true);
    try {
      const result = await api.post<{ payments: DebtPaymentEntry[] }>(
        `/debts/${selectedProfileId}/compute`,
        { savings_margin: parseFloat(savingsMargin) || 0 }
      );
      setComputedPayments(result.payments);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to compute payments');
    } finally {
      setComputing(false);
    }
  };

  const handleSavePayments = async () => {
    if (!selectedProfileId || !computedPayments) return;
    setSavingPayments(true);
    try {
      const result = await api.post<{ success: boolean; count: number }>(
        `/debts/${selectedProfileId}/save_payments`,
        { payments: computedPayments }
      );
      setSnackbar(`Saved ${result.count} payment(s)`);
      setComputeDialogVisible(false);
      setComputedPayments(null);
      await fetchData();
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save payments');
    } finally {
      setSavingPayments(false);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────

  const renderDebtItem = ({ item }: { item: Debt }) => {
    const pctPaid = item.total_amount > 0
      ? ((item.total_amount - item.remaining_amount) / item.total_amount) * 100
      : 0;

    return (
      <List.Item
        title={item.name}
        description={`$${item.remaining_amount.toFixed(2)} / $${item.total_amount.toFixed(2)}  ·  ${item.interest_rate}% APR  ·  Min $${item.min_payment.toFixed(2)}`}
        onPress={() => openEditDialog(item)}
        right={() => (
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={[styles.pctText, { color: theme.colors.primary }]}>{pctPaid.toFixed(0)}%</Text>
            <IconButton icon="delete" size={20} onPress={() => openDeleteDialog(item)} />
          </View>
        )}
      />
    );
  };

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.headerRow}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text variant="titleLarge">Debts</Text>
            <HelpIcon text="Track debts and interest rates. Budgie can compute optimal payment plans from your surplus." />
          </View>
          {selectedProfileId && debts.length > 0 && (
            <Button
              mode="outlined"
              icon="calculator"
              onPress={openComputeDialog}
              compact
              style={[styles.computeButton, { borderColor: theme.colors.primary }]}
            >
              Compute Payments
            </Button>
          )}
        </View>

        {!selectedProfileId ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            Select a profile in Settings to view debts
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
        ) : debts.length === 0 && !loading ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No debts yet.{'\n\n'}Track loans, credit cards, and other debts here. Budgie can compute optimal payment plans from your budget surplus.{'\n\n'}Tap the + button to add your first debt.
          </Text>
        ) : (
          <FlatList
            data={debts}
            keyExtractor={(item) => String(item.id)}
            renderItem={renderDebtItem}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchData(true)}
                colors={[theme.colors.primary]}
              />
            }
          />
        )}
      </View>

      {/* ── Add/Edit Dialog ──────────────────────────────────────────────── */}
      <Portal>
        <Dialog visible={formVisible} onDismiss={() => setFormVisible(false)}>
          <Dialog.Title>{editingDebt ? 'Edit Debt' : 'Add Debt'}</Dialog.Title>
          <Dialog.ScrollArea style={styles.dialogScroll}>
            <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
              <TextInput
                label="Name"
                value={form.name}
                onChangeText={(v) => setForm({ ...form, name: v })}
                mode="outlined"
                style={styles.dialogInput}
              />
              <TextInput
                label="Total Amount"
                value={form.total_amount}
                onChangeText={(v) => setForm({ ...form, total_amount: v })}
                mode="outlined"
                keyboardType="decimal-pad"
                style={styles.dialogInput}
              />
              <TextInput
                label="Remaining Amount"
                value={form.remaining_amount}
                onChangeText={(v) => setForm({ ...form, remaining_amount: v })}
                mode="outlined"
                keyboardType="decimal-pad"
                style={styles.dialogInput}
              />
              <TextInput
                label="Min Payment"
                value={form.min_payment}
                onChangeText={(v) => setForm({ ...form, min_payment: v })}
                mode="outlined"
                keyboardType="decimal-pad"
                style={styles.dialogInput}
              />
              <TextInput
                label="Interest Rate (%)"
                value={form.interest_rate}
                onChangeText={(v) => setForm({ ...form, interest_rate: v })}
                mode="outlined"
                keyboardType="decimal-pad"
                style={styles.dialogInput}
              />
            </KeyboardAvoidingView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setFormVisible(false)}>Cancel</Button>
            <Button onPress={handleSave} loading={saving} disabled={saving}>
              {editingDebt ? 'Save Changes' : 'Add Debt'}
            </Button>
          </Dialog.Actions>
        </Dialog>

        {/* ── Delete Dialog ────────────────────────────────────────────── */}
        <Dialog visible={deleteDialogVisible} onDismiss={() => setDeleteDialogVisible(false)}>
          <Dialog.Title>Delete Debt</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">Delete "{deletingDebt?.name}"? This cannot be undone.</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteDialogVisible(false)}>Cancel</Button>
            <Button textColor={theme.colors.error} onPress={handleDelete} loading={deleting} disabled={deleting}>
              Delete
            </Button>
          </Dialog.Actions>
        </Dialog>

        {/* ── Compute Payments Dialog ──────────────────────────────────── */}
        <Dialog
          visible={computeDialogVisible}
          onDismiss={() => { setComputeDialogVisible(false); setComputedPayments(null); }}
        >
          <Dialog.Title>Compute Debt Payments</Dialog.Title>
          <Dialog.ScrollArea style={styles.computeScroll}>
            <View>
              <TextInput
                label="Savings Margin ($)"
                value={savingsMargin}
                onChangeText={setSavingsMargin}
                mode="outlined"
                keyboardType="decimal-pad"
                style={styles.dialogInput}
              />
              <Button
                mode="contained"
                onPress={handleCompute}
                loading={computing}
                disabled={computing}
                style={styles.computeRunButton}
              >
                Compute
              </Button>

              {computedPayments && computedPayments.length > 0 && (
                <View style={styles.paymentsTable}>
                  <Text variant="titleSmall" style={[styles.paymentsTitle, { color: theme.colors.primary }]}>Payment Plan</Text>
                  <DataTable>
                    <DataTable.Header>
                      <DataTable.Title>Debt</DataTable.Title>
                      <DataTable.Title numeric>Amount</DataTable.Title>
                      <DataTable.Title>Date</DataTable.Title>
                    </DataTable.Header>
                    {computedPayments.map((p, i) => (
                      <DataTable.Row key={i}>
                        <DataTable.Cell>{p.debt_name}</DataTable.Cell>
                        <DataTable.Cell numeric>${p.amount.toFixed(2)}</DataTable.Cell>
                        <DataTable.Cell>{p.income_date}</DataTable.Cell>
                      </DataTable.Row>
                    ))}
                  </DataTable>
                </View>
              )}

              {computedPayments && computedPayments.length === 0 && (
                <Text variant="bodyMedium" style={styles.emptyPayments}>
                  No payments computed. Check your savings margin and debt balances.
                </Text>
              )}
            </View>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => { setComputeDialogVisible(false); setComputedPayments(null); }}>
              Cancel
            </Button>
            {computedPayments && computedPayments.length > 0 && (
              <Button onPress={handleSavePayments} loading={savingPayments} disabled={savingPayments}>
                Save Payments
              </Button>
            )}
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={2000}>
        {snackbar}
      </Snackbar>

      {selectedProfileId && (
        <FAB
          icon="plus"
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          color={theme.colors.background}
          onPress={openAddDialog}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {},
  computeButton: {},
  loader: { marginTop: 32 },
  errorText: { marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  pctText: {
    alignSelf: 'center',
    fontVariant: ['tabular-nums'],
    fontSize: 14,
    marginRight: 4,
  },
  dialogScroll: { maxHeight: 400 },
  dialogInput: { marginBottom: 12 },
  computeScroll: { maxHeight: 480 },
  computeRunButton: { marginTop: 4, marginBottom: 16 },
  paymentsTable: { marginTop: 8 },
  paymentsTitle: { marginBottom: 8 },
  emptyPayments: { opacity: 0.7, marginTop: 12, textAlign: 'center' },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});
