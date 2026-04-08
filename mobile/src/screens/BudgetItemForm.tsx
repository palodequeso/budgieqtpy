import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Snackbar,
  SegmentedButtons,
  Dialog,
  Portal,
  RadioButton,
  Switch,
  Divider,
  IconButton,
  useTheme,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { BudgetStackParamList } from '../navigation/BudgetStack';
import { useStore, BudgetGroup } from '../store/store';
import { api } from '../api/api';

type Props = NativeStackScreenProps<BudgetStackParamList, 'BudgetItemForm'>;

const PERIOD_TYPES = ['Monthly', 'Weekly', 'Biweekly', 'Daily'] as const;
type PeriodType = (typeof PERIOD_TYPES)[number];
type BusinessDay = '' | 'Previous' | 'Next';

interface PeriodEntry {
  type: PeriodType;
  monthlyValue: string; // "1st"…"28th" | "Last"
  businessDay: BusinessDay;
}

function toOrdinal(n: number): string {
  const s = n % 100;
  if (s >= 11 && s <= 13) return `${n}th`;
  switch (n % 10) {
    case 1: return `${n}st`;
    case 2: return `${n}nd`;
    case 3: return `${n}rd`;
    default: return `${n}th`;
  }
}

const MONTHLY_DAY_OPTIONS = [
  ...Array.from({ length: 28 }, (_, i) => toOrdinal(i + 1)),
  'Last',
];

function periodSummary(p: PeriodEntry): string {
  if (p.type !== 'Monthly') return p.type;
  let s = `Monthly · ${p.monthlyValue}`;
  if (p.businessDay === 'Previous') s += ' · Prev BD';
  else if (p.businessDay === 'Next') s += ' · Next BD';
  return s;
}

function initPeriods(item?: Props['route']['params']['item']): PeriodEntry[] {
  if (!item?.periods?.length) {
    return [{ type: 'Monthly', monthlyValue: '1st', businessDay: '' }];
  }
  return item.periods.map((p) => ({
    type: (p.type as PeriodType) ?? 'Monthly',
    monthlyValue: p.type === 'Monthly' ? (String(p.value) || '1st') : '1st',
    businessDay: ((p.businessDay ?? '') as BusinessDay),
  }));
}

const todayStr = () => new Date().toISOString().slice(0, 10);
const farFutureStr = () => '2999-12-31';

export default function BudgetItemForm({ route, navigation }: Props) {
  const { groups: initialGroups, item } = route.params;
  const isEdit = !!item;
  const { selectedProfileId } = useStore();
  const theme = useTheme();

  // ── Form state ──────────────────────────────────────────────────────────────
  const [name, setName] = useState(item?.name ?? '');
  const [amount, setAmount] = useState(item?.amount?.toString() ?? '');
  const [itemType, setItemType] = useState<'expense' | 'income'>(
    (item?.type?.toLowerCase() as 'expense' | 'income') ?? 'expense'
  );
  const [groups, setGroups] = useState<BudgetGroup[]>(initialGroups);
  const [groupId, setGroupId] = useState<number | null>(item?.budget_group_id ?? initialGroups[0]?.id ?? null);
  const [debtId, setDebtId] = useState<number | null>(item?.debt_id ?? null);
  const [debts, setDebts] = useState<Array<{ id: number; name: string; remaining_amount: number }>>([]);
  const [debtPickerVisible, setDebtPickerVisible] = useState(false);
  const [startDate, setStartDate] = useState(item?.start_date?.slice(0, 10) ?? todayStr());
  const [noEndDate, setNoEndDate] = useState(
    !item?.end_date || new Date(item.end_date).getFullYear() > 2100
  );
  const [endDate, setEndDate] = useState(
    item?.end_date && new Date(item.end_date).getFullYear() <= 2100
      ? item.end_date.slice(0, 10)
      : ''
  );

  // ── Period state ──────────────────────────────────────────────────────────
  const [periods, setPeriods] = useState<PeriodEntry[]>(() => initPeriods(item));

  // Period editor dialog
  const [periodEditorVisible, setPeriodEditorVisible] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null); // null = adding new
  const [editType, setEditType] = useState<PeriodType>('Monthly');
  const [editMonthlyValue, setEditMonthlyValue] = useState('1st');
  const [editBusinessDay, setEditBusinessDay] = useState<BusinessDay>('');

  const openPeriodEditor = (index: number | null) => {
    if (index !== null) {
      const p = periods[index];
      setEditType(p.type);
      setEditMonthlyValue(p.monthlyValue);
      setEditBusinessDay(p.businessDay);
    } else {
      setEditType('Monthly');
      setEditMonthlyValue('1st');
      setEditBusinessDay('');
    }
    setEditingIndex(index);
    setPeriodEditorVisible(true);
  };

  const commitPeriodEdit = () => {
    const entry: PeriodEntry = {
      type: editType,
      monthlyValue: editMonthlyValue,
      businessDay: editType === 'Monthly' ? editBusinessDay : '',
    };
    if (editingIndex !== null) {
      setPeriods((prev) => prev.map((p, i) => (i === editingIndex ? entry : p)));
    } else {
      setPeriods((prev) => [...prev, entry]);
    }
    setPeriodEditorVisible(false);
  };

  const removePeriod = (index: number) => {
    setPeriods((prev) => prev.filter((_, i) => i !== index));
  };

  // ── UI state ─────────────────────────────────────────────────────────────────
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [snackbar, setSnackbar] = useState('');
  const [groupPickerVisible, setGroupPickerVisible] = useState(false);
  const [extrapolateDialogVisible, setExtrapolateDialogVisible] = useState(false);
  const [extrapolating, setExtrapolating] = useState(false);
  const [deleteDialogVisible, setDeleteDialogVisible] = useState(false);

  // ── Fetch debts on mount ─────────────────────────────────────────────────────
  React.useEffect(() => {
    if (selectedProfileId) {
      api.get<Array<{ id: number; name: string; remaining_amount: number }>>(`/debts/${selectedProfileId}`)
        .then((data) => setDebts(data || []))
        .catch(() => setDebts([]));
    }
  }, [selectedProfileId]);

  // ── Inline group creation ────────────────────────────────────────────────────
  const [newGroupName, setNewGroupName] = useState('');
  const [creatingGroup, setCreatingGroup] = useState(false);

  const handleCreateGroup = async () => {
    if (!selectedProfileId || !newGroupName.trim()) return;
    setCreatingGroup(true);
    try {
      const created = await api.post<{ id: number; name: string }>(
        `/budget/group/${selectedProfileId}`,
        { name: newGroupName.trim() }
      );
      const newGroup: BudgetGroup = { id: created.id, name: created.name };
      setGroups((prev) => [...prev, newGroup]);
      setGroupId(created.id);
      setNewGroupName('');
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to create group');
    } finally {
      setCreatingGroup(false);
    }
  };

  // ── Save ─────────────────────────────────────────────────────────────────────
  const handleSave = async () => {
    if (!selectedProfileId) return;
    if (!name.trim()) { setSnackbar('Name is required'); return; }
    if (!amount || isNaN(parseFloat(amount))) { setSnackbar('Amount must be a number'); return; }
    if (!startDate || startDate.length !== 10) { setSnackbar('Start date must be YYYY-MM-DD'); return; }
    if (!noEndDate && (!endDate || endDate.length !== 10)) { setSnackbar('End date must be YYYY-MM-DD'); return; }
    if (groupId == null) { setSnackbar('Select a budget group'); return; }
    if (periods.length === 0) { setSnackbar('Add at least one schedule'); return; }

    const resolvedEndDate = noEndDate ? farFutureStr() : endDate;
    const periodsPayload = periods.map((p) => ({
      type: p.type,
      value: p.type === 'Monthly' ? p.monthlyValue : '1',
      business_day: p.businessDay,
    }));

    setSaving(true);
    try {
      const body = {
        name: name.trim(),
        amount: parseFloat(amount),
        type: itemType,
        budget_group_id: groupId,
        start_date: startDate,
        end_date: resolvedEndDate,
        periods: periodsPayload,
        debt_id: debtId,
      };
      if (isEdit) {
        await api.put(`/budget/${selectedProfileId}/${item!.id}`, body);
        setSnackbar('Budget item updated');
        setTimeout(() => navigation.goBack(), 800);
      } else {
        await api.post(`/budget/${selectedProfileId}`, body);
        setExtrapolateDialogVisible(true);
      }
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to save budget item');
    } finally {
      setSaving(false);
    }
  };

  // ── Delete ───────────────────────────────────────────────────────────────────
  const handleDelete = async () => {
    if (!selectedProfileId || !item) return;
    setDeleting(true);
    try {
      await api.del(`/budget/${selectedProfileId}/${item.id}`);
      setDeleteDialogVisible(false);
      setSnackbar('Budget item deleted');
      setTimeout(() => navigation.goBack(), 600);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to delete item');
    } finally {
      setDeleting(false);
    }
  };

  // ── Extrapolate after create ─────────────────────────────────────────────────
  const handleExtrapolate = async () => {
    if (!selectedProfileId) return;
    setExtrapolating(true);
    try {
      const result = await api.post<{ success: boolean; count: number }>(
        `/extrapolate/${selectedProfileId}`,
        { profileID: selectedProfileId }
      );
      setExtrapolateDialogVisible(false);
      setSnackbar(`Extrapolation complete — ${result.count} items scheduled`);
      setTimeout(() => navigation.goBack(), 1500);
    } catch (e: any) {
      setSnackbar(e.message ?? 'Extrapolation failed');
    } finally {
      setExtrapolating(false);
    }
  };

  const selectedGroup = groups.find((g) => g.id === groupId);
  const selectedDebt = debts.find((d) => d.id === debtId);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={[styles.container, { backgroundColor: theme.colors.background }]} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Button icon="arrow-left" mode="text" onPress={() => navigation.goBack()} style={styles.backButton}>
              Back
            </Button>
            <Text variant="titleLarge">{isEdit ? 'Edit Budget Item' : 'Add Budget Item'}</Text>
          </View>

          <TextInput label="Name" value={name} onChangeText={setName} mode="outlined" style={styles.input} />

          <TextInput
            label="Amount"
            value={amount}
            onChangeText={setAmount}
            mode="outlined"
            keyboardType="decimal-pad"
            style={styles.input}
          />

          <Text variant="labelMedium" style={[styles.fieldLabel, { color: theme.colors.onSurfaceVariant }]}>Type</Text>
          <SegmentedButtons
            value={itemType}
            onValueChange={(v) => setItemType(v as 'expense' | 'income')}
            buttons={[{ value: 'expense', label: 'Expense' }, { value: 'income', label: 'Income' }]}
            style={styles.segmented}
          />

          <Button
            mode="outlined"
            onPress={() => setGroupPickerVisible(true)}
            style={[styles.pickerButton, { borderColor: theme.colors.primary }]}
            contentStyle={styles.pickerButtonContent}
          >
            Group: {selectedGroup?.name ?? 'Select group'}
          </Button>

          {debts.length > 0 && (
            <Button
              mode="outlined"
              onPress={() => setDebtPickerVisible(true)}
              style={[styles.pickerButton, { borderColor: theme.colors.primary }]}
              contentStyle={styles.pickerButtonContent}
            >
              Linked Debt: {selectedDebt ? selectedDebt.name : 'None'}
            </Button>
          )}

          <TextInput
            label="Start date (YYYY-MM-DD)"
            value={startDate}
            onChangeText={setStartDate}
            mode="outlined"
            style={styles.input}
          />

          <View style={styles.switchRow}>
            <Text variant="bodyMedium">No end date</Text>
            <Switch value={noEndDate} onValueChange={setNoEndDate} color={theme.colors.primary} />
          </View>

          {!noEndDate && (
            <TextInput
              label="End date (YYYY-MM-DD)"
              value={endDate}
              onChangeText={setEndDate}
              mode="outlined"
              style={styles.input}
            />
          )}

          {/* ── Schedules ─────────────────────────────────────────────────── */}
          <Text variant="labelMedium" style={[styles.fieldLabel, { color: theme.colors.onSurfaceVariant }]}>Schedules</Text>
          {periods.map((p, i) => (
            <View key={i} style={[styles.periodRow, { backgroundColor: theme.colors.surfaceVariant }]}>
              <Text variant="bodyMedium" style={styles.periodText}>{periodSummary(p)}</Text>
              <View style={styles.periodActions}>
                <IconButton icon="pencil" size={18} onPress={() => openPeriodEditor(i)} style={styles.periodIcon} />
                {periods.length > 1 && (
                  <IconButton icon="close" size={18} onPress={() => removePeriod(i)} style={styles.periodIcon} />
                )}
              </View>
            </View>
          ))}
          <Button
            mode="outlined"
            icon="plus"
            onPress={() => openPeriodEditor(null)}
            style={[styles.addScheduleButton, { borderColor: theme.colors.primary }]}
            contentStyle={styles.pickerButtonContent}
          >
            Add Schedule
          </Button>

          <Button
            mode="contained"
            onPress={handleSave}
            loading={saving}
            disabled={saving}
            style={styles.saveButton}
          >
            {isEdit ? 'Save Changes' : 'Save Budget Item'}
          </Button>

          {isEdit && (
            <Button
              mode="outlined"
              onPress={() => setDeleteDialogVisible(true)}
              style={[styles.deleteButton, { borderColor: theme.colors.error }]}
              textColor={theme.colors.error}
            >
              Delete Item
            </Button>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

      <Portal>
        {/* Group picker with inline creation */}
        <Dialog visible={groupPickerVisible} onDismiss={() => setGroupPickerVisible(false)}>
          <Dialog.Title>Select Group</Dialog.Title>
          <Dialog.ScrollArea style={styles.groupScrollArea}>
            <ScrollView>
              <RadioButton.Group
                value={groupId != null ? String(groupId) : ''}
                onValueChange={(v) => setGroupId(Number(v))}
              >
                {groups.map((g) => (
                  <RadioButton.Item key={g.id} label={g.name} value={String(g.id)} />
                ))}
              </RadioButton.Group>

              <Divider style={styles.groupDivider} />
              <Text variant="labelMedium" style={[styles.newGroupLabel, { color: theme.colors.onSurfaceVariant }]}>New group</Text>
              <View style={styles.newGroupRow}>
                <TextInput
                  value={newGroupName}
                  onChangeText={setNewGroupName}
                  mode="outlined"
                  placeholder="Group name"
                  dense
                  style={styles.newGroupInput}
                />
                <Button
                  mode="contained"
                  onPress={handleCreateGroup}
                  loading={creatingGroup}
                  disabled={creatingGroup || !newGroupName.trim()}
                  compact
                  style={styles.newGroupButton}
                >
                  Add
                </Button>
              </View>
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setGroupPickerVisible(false)}>Done</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Debt picker */}
        <Dialog visible={debtPickerVisible} onDismiss={() => setDebtPickerVisible(false)}>
          <Dialog.Title>Linked Debt (Optional)</Dialog.Title>
          <Dialog.ScrollArea style={styles.groupScrollArea}>
            <ScrollView>
              <RadioButton.Group
                value={debtId != null ? String(debtId) : ''}
                onValueChange={(v) => setDebtId(v ? Number(v) : null)}
              >
                <RadioButton.Item label="None" value="" />
                {debts.map((d) => (
                  <RadioButton.Item
                    key={d.id}
                    label={`${d.name} ($${parseFloat(String(d.remaining_amount)).toFixed(2)} remaining)`}
                    value={String(d.id)}
                  />
                ))}
              </RadioButton.Group>
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setDebtPickerVisible(false)}>Done</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Period editor */}
        <Dialog visible={periodEditorVisible} onDismiss={() => setPeriodEditorVisible(false)}>
          <Dialog.Title>{editingIndex !== null ? 'Edit Schedule' : 'Add Schedule'}</Dialog.Title>
          <Dialog.ScrollArea style={styles.periodScrollArea}>
            <ScrollView>
              <Text variant="labelMedium" style={[styles.dialogSectionLabel, { color: theme.colors.onSurfaceVariant }]}>Type</Text>
              <RadioButton.Group
                value={editType}
                onValueChange={(v) => setEditType(v as PeriodType)}
              >
                {PERIOD_TYPES.map((t) => (
                  <RadioButton.Item key={t} label={t} value={t} />
                ))}
              </RadioButton.Group>

              {editType === 'Monthly' && (
                <>
                  <Divider style={styles.dialogDivider} />
                  <Text variant="labelMedium" style={[styles.dialogSectionLabel, { color: theme.colors.onSurfaceVariant }]}>Day of Month</Text>
                  <RadioButton.Group
                    value={editMonthlyValue}
                    onValueChange={setEditMonthlyValue}
                  >
                    {MONTHLY_DAY_OPTIONS.map((d) => (
                      <RadioButton.Item key={d} label={d} value={d} />
                    ))}
                  </RadioButton.Group>

                  <Divider style={styles.dialogDivider} />
                  <Text variant="labelMedium" style={[styles.dialogSectionLabel, { color: theme.colors.onSurfaceVariant }]}>Business Day Adjustment</Text>
                  <RadioButton.Group
                    value={editBusinessDay}
                    onValueChange={(v) => setEditBusinessDay(v as BusinessDay)}
                  >
                    <RadioButton.Item label="None" value="" />
                    <RadioButton.Item label="Previous business day" value="Previous" />
                    <RadioButton.Item label="Next business day" value="Next" />
                  </RadioButton.Group>
                </>
              )}
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setPeriodEditorVisible(false)}>Cancel</Button>
            <Button onPress={commitPeriodEdit}>Done</Button>
          </Dialog.Actions>
        </Dialog>

        {/* Extrapolate after create */}
        <Dialog visible={extrapolateDialogVisible} onDismiss={() => { setExtrapolateDialogVisible(false); navigation.goBack(); }}>
          <Dialog.Title>Budget item saved</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">Run extrapolation now to schedule this item into the calendar?</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => { setExtrapolateDialogVisible(false); navigation.goBack(); }}>Skip</Button>
            <Button onPress={handleExtrapolate} loading={extrapolating} disabled={extrapolating}>
              Run Extrapolation
            </Button>
          </Dialog.Actions>
        </Dialog>

        {/* Delete confirm */}
        <Dialog visible={deleteDialogVisible} onDismiss={() => setDeleteDialogVisible(false)}>
          <Dialog.Title>Delete Budget Item</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">Delete "{item?.name}"? This cannot be undone.</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteDialogVisible(false)}>Cancel</Button>
            <Button textColor={theme.colors.error} onPress={handleDelete} loading={deleting} disabled={deleting}>
              Delete
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar visible={!!snackbar} onDismiss={() => setSnackbar('')} duration={3000}>{snackbar}</Snackbar>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  container: { padding: 16, flexGrow: 1 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: 20, gap: 8 },
  backButton: { marginLeft: -8 },
  input: { marginBottom: 12 },
  fieldLabel: { marginBottom: 6, marginTop: 4 },
  segmented: { marginBottom: 12 },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  pickerButton: { marginBottom: 12, borderColor: '#4fc3f7' },
  pickerButtonContent: { justifyContent: 'flex-start' },
  periodRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#263545',
    borderRadius: 8,
    paddingLeft: 12,
    paddingVertical: 4,
    marginBottom: 8,
  },
  periodText: { flex: 1 },
  periodActions: { flexDirection: 'row' },
  periodIcon: { margin: 0 },
  addScheduleButton: { marginBottom: 12, borderColor: '#4fc3f7' },
  saveButton: { marginTop: 8 },
  deleteButton: { marginTop: 10, borderColor: '#ef5350' },
  groupScrollArea: { maxHeight: 320 },
  groupDivider: { marginVertical: 12 },
  newGroupLabel: { color: '#90a4ae', marginBottom: 8, paddingHorizontal: 4 },
  newGroupRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 4 },
  newGroupInput: { flex: 1 },
  newGroupButton: { marginTop: 2 },
  periodScrollArea: { maxHeight: 420 },
  dialogSectionLabel: { color: '#90a4ae', marginBottom: 4, marginTop: 8, paddingHorizontal: 4 },
  dialogDivider: { marginVertical: 8 },
});
