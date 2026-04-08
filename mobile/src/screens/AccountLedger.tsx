import React, { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, List, Divider, ActivityIndicator, Button, FAB, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AccountsStackParamList } from '../navigation/AccountsStack';
import { useStore, LedgerEntry, Profile } from '../store/store';
import { api } from '../api/api';

type Props = NativeStackScreenProps<AccountsStackParamList, 'AccountLedger'>;

export default function AccountLedger({ route, navigation }: Props) {
  const { account } = route.params;
  const { selectedProfileId, setAccounts } = useStore();
  const theme = useTheme();

  const [ledgerEntries, setLedgerEntries] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [currentBalance, setCurrentBalance] = useState<number>(account.balance);

  const fetchLedger = useCallback(async (isRefresh = false) => {
    if (!selectedProfileId) return;
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const profile = await api.get<Profile>(`/profiles/${selectedProfileId}`);
      const acct = profile.accounts.find(a => a.id === account.id);
      if (acct) {
        setLedgerEntries(acct.ledger);
        setCurrentBalance(acct.balance);
      }
      setAccounts(profile.accounts);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load ledger');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedProfileId, account.id, setAccounts]);

  useEffect(() => {
    fetchLedger();
  }, [fetchLedger]);

  const sorted = [...ledgerEntries].sort((a, b) => b.paid_date.localeCompare(a.paid_date));

  const amountColor = (amount: number) => amount < 0 ? theme.colors.error : '#66bb6a';

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.colors.surface }]}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.header}>
          <Text variant="titleLarge" style={styles.title}>{account.name}</Text>
          <Text variant="bodySmall" style={styles.subtitle}>
            {account.type} · <Text style={{ color: amountColor(currentBalance) }}>{currentBalance.toFixed(2)}</Text>
          </Text>
        </View>

        {loading && !refreshing ? (
          <ActivityIndicator animating={true} color={theme.colors.primary} style={styles.loader} />
        ) : error ? (
          <View>
            <Text variant="bodySmall" style={[styles.errorText, { color: theme.colors.error }]}>{error}</Text>
            <Button mode="outlined" onPress={() => fetchLedger()} style={styles.retryButton}>
              Retry
            </Button>
          </View>
        ) : sorted.length === 0 && !loading ? (
          <Text variant="bodyMedium" style={styles.emptyText}>
            No ledger entries yet.{'\n\n'}Ledger entries are individual transactions — payments, deposits, refunds. Tap the + button to add one, or mark items as paid from the Calendar.
          </Text>
        ) : (
          <ScrollView
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchLedger(true)}
                colors={[theme.colors.primary]}
              />
            }
          >
            {sorted.map((entry, index) => (
              <React.Fragment key={entry.id}>
                <List.Item
                  title={entry.name}
                  description={entry.paid_date}
                  right={() => (
                    <Text style={{ color: amountColor(entry.amount), fontVariant: ['tabular-nums'], alignSelf: 'center', marginRight: 8 }}>
                      {entry.amount.toFixed(2)}
                    </Text>
                  )}
                  onPress={() =>
                    navigation.navigate('LedgerForm', {
                      accountId: account.id,
                      profileId: selectedProfileId!,
                      ledgerEntry: entry,
                    })
                  }
                />
                {index < sorted.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </ScrollView>
        )}
      </View>

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        onPress={() =>
          navigation.navigate('LedgerForm', {
            accountId: account.id,
            profileId: selectedProfileId!,
          })
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: { flex: 1, padding: 16 },
  header: { marginBottom: 16 },
  title: { marginBottom: 4 },
  subtitle: { opacity: 0.8 },
  loader: { marginTop: 32 },
  errorText: { marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  emptyText: { opacity: 0.7, marginTop: 16 },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});
