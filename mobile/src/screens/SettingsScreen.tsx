import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform, Share } from 'react-native';
import { TextInput, Button, Text, Snackbar, ActivityIndicator, List, Divider, Switch, Portal, Dialog, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useStore } from '../store/store';
import { api } from '../api/api';

interface ProfileListItem {
  id: number;
  name: string;
}

export default function SettingsScreen() {
  const { serverUrl, setServerUrl, selectedProfileId, setSelectedProfileId, themeMode, setThemeMode, setOnboardingCompleted } = useStore();
  const theme = useTheme();

  const [draft, setDraft] = useState(serverUrl ?? '');
  const [saved, setSaved] = useState(false);

  const [profiles, setProfiles] = useState<ProfileListItem[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [newProfileName, setNewProfileName] = useState('');
  const [creatingProfile, setCreatingProfile] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<ProfileListItem | null>(null);

  // ── Export/Import ────────────────────────────────────────────────────────
  const [exportLoading, setExportLoading] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [importDialogVisible, setImportDialogVisible] = useState(false);
  const [importJson, setImportJson] = useState('');
  const [importError, setImportError] = useState<string | null>(null);

  const handleExportProfile = async () => {
    if (!selectedProfileId) return;
    setExportLoading(true);
    try {
      const data = await api.get(`/profile/${selectedProfileId}/export`);
      const jsonStr = JSON.stringify(data, null, 2);
      await Share.share({
        message: jsonStr,
        title: 'Budgie Profile Export',
      });
      setSnackbar('Profile exported');
    } catch (e: any) {
      setSnackbar(e.message ?? 'Failed to export profile');
    } finally {
      setExportLoading(false);
    }
  };

  const handleImportProfile = async () => {
    if (!importJson.trim()) return;
    setImportLoading(true);
    setImportError(null);
    try {
      const jsonData = JSON.parse(importJson);
      const result = await api.post<any>('/profile/import', jsonData);
      const newName = result?.name || result?.profile?.name || 'Imported profile';
      setImportDialogVisible(false);
      setImportJson('');
      setSnackbar(`Profile "${newName}" imported`);
      await fetchProfiles();
    } catch (e: any) {
      if (e instanceof SyntaxError) {
        setImportError('Invalid JSON. Please paste a valid profile export.');
      } else {
        setImportError(e.message ?? 'Failed to import profile');
      }
    } finally {
      setImportLoading(false);
    }
  };

  // ── AI settings ──────────────────────────────────────────────────────────
  const [aiServerUrl, setAiServerUrl] = useState('');
  const [aiModel, setAiModel] = useState('qwen2.5:0.5b');
  const [aiEnabled, setAiEnabled] = useState(false);
  const [snackbar, setSnackbar] = useState('');

  const fetchProfiles = async () => {
    if (!serverUrl) return;
    setLoadingProfiles(true);
    setProfileError(null);
    try {
      const data = await api.get<ProfileListItem[]>('/profiles');
      setProfiles(data);
    } catch (e: any) {
      setProfileError(e.message ?? 'Failed to load profiles');
    } finally {
      setLoadingProfiles(false);
    }
  };

  useEffect(() => {
    if (serverUrl) fetchProfiles();
  }, [serverUrl]);

  useEffect(() => {
    api.get('/ai/config').then((config: any) => {
      setAiServerUrl(config.server_url || '');
      setAiModel(config.model || 'qwen2.5:0.5b');
      setAiEnabled(config.enabled || false);
    }).catch(() => {});
  }, []);

  const handleCreateProfile = async () => {
    if (!newProfileName.trim()) return;
    setCreatingProfile(true);
    try {
      const created = await api.post<ProfileListItem>('/profiles', { name: newProfileName.trim() });
      setNewProfileName('');
      await fetchProfiles();
      setSelectedProfileId(created.id);
      setSnackbar('Profile created');
    } catch (e: any) {
      setProfileError(e.message ?? 'Failed to create profile');
    } finally {
      setCreatingProfile(false);
    }
  };

  const handleDeleteProfile = async (p: ProfileListItem) => {
    try {
      await api.delete(`/profiles/${p.id}`);
      setDeleteConfirm(null);
      if (selectedProfileId === p.id) setSelectedProfileId(null);
      await fetchProfiles();
      setSnackbar(`Profile "${p.name}" deleted`);
    } catch (e: any) {
      setProfileError(e.message ?? 'Failed to delete profile');
      setDeleteConfirm(null);
    }
  };

  const saveAiConfig = async () => {
    try {
      await api.put('/ai/config', {
        server_url: aiServerUrl,
        model: aiModel,
        enabled: aiEnabled,
      });
      setSnackbar('AI settings saved');
    } catch {
      setSnackbar('Failed to save AI settings');
    }
  };

  function handleSave() {
    setServerUrl(draft.trim());
    setSaved(true);
  }

  const activeProfile = profiles.find((p) => p.id === selectedProfileId);

  const dynamicStyles = StyleSheet.create({
    safe: { flex: 1, backgroundColor: theme.colors.surface },
    container: {
      backgroundColor: theme.colors.background,
      padding: 16,
      flexGrow: 1,
    },
    selectedItem: { backgroundColor: theme.dark ? '#3a4859' : '#e3f2fd' },
  });

  return (
    <SafeAreaView style={dynamicStyles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={dynamicStyles.container} keyboardShouldPersistTaps="handled">
          <Text variant="titleLarge" style={styles.title}>Settings</Text>

          {/* Section 1: Server URL */}
          <TextInput
            label="Server URL"
            value={draft}
            onChangeText={setDraft}
            mode="outlined"
            keyboardType="url"
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="http://192.168.1.10:8000"
            style={styles.input}
          />

          <Text variant="bodySmall" style={styles.helper}>
            Current: {serverUrl ?? 'Not set'}
          </Text>

          <Button mode="contained" onPress={handleSave} style={styles.button}>
            Save
          </Button>

          <Divider style={styles.divider} />

          {/* Section 2: Theme */}
          <Text variant="titleMedium" style={styles.sectionTitle}>Theme</Text>
          <View style={styles.switchRow}>
            <Text variant="bodyMedium">Dark Mode</Text>
            <Switch
              value={themeMode === 'dark'}
              onValueChange={(value) => setThemeMode(value ? 'dark' : 'light')}
            />
          </View>

          <Divider style={styles.divider} />

          {/* Section 3: Profile Selection */}
          <Text variant="titleMedium" style={styles.sectionTitle}>Profiles</Text>

          {!serverUrl ? (
            <Text variant="bodySmall" style={styles.emptyText}>
              Enter a server URL above to load profiles
            </Text>
          ) : loadingProfiles ? (
            <ActivityIndicator animating={true} color={theme.colors.primary} style={styles.loader} />
          ) : profileError ? (
            <View>
              <Text variant="bodySmall" style={styles.errorText}>{profileError}</Text>
              <Button mode="outlined" onPress={fetchProfiles} style={styles.retryButton}>
                Retry
              </Button>
            </View>
          ) : profiles.length === 0 ? (
            <Text variant="bodySmall" style={styles.emptyText}>
              No profiles found on server
            </Text>
          ) : (
            profiles.map((p) => (
              <List.Item
                key={p.id}
                title={p.name}
                onPress={() => setSelectedProfileId(p.id)}
                right={() => (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {selectedProfileId === p.id && <List.Icon icon="check" color={theme.colors.primary} />}
                    <Button
                      compact
                      mode="text"
                      textColor={theme.colors.error}
                      onPress={() => setDeleteConfirm(p)}
                      icon="delete"
                      children=""
                    />
                  </View>
                )}
                style={selectedProfileId === p.id ? dynamicStyles.selectedItem : undefined}
              />
            ))
          )}

          {profiles.length > 0 && (
            <Text variant="bodySmall" style={styles.activeText}>
              Active: {activeProfile?.name ?? 'None selected'}
            </Text>
          )}

          <Divider style={styles.divider} />
          <Text variant="titleMedium" style={styles.sectionTitle}>Create Profile</Text>
          <TextInput
            label="Profile name"
            value={newProfileName}
            onChangeText={setNewProfileName}
            mode="outlined"
            style={styles.input}
          />
          <Button
            mode="outlined"
            onPress={handleCreateProfile}
            loading={creatingProfile}
            disabled={creatingProfile || !newProfileName.trim() || !serverUrl}
            style={styles.button}
          >
            Create Profile
          </Button>

          <Divider style={styles.divider} />

          {/* Section 4: Export & Import */}
          <Text variant="titleMedium" style={styles.sectionTitle}>Export &amp; Import</Text>
          <Text variant="bodySmall" style={styles.helper}>
            Export your current profile as JSON, or import a previously exported profile.
          </Text>
          <Button
            mode="contained"
            onPress={handleExportProfile}
            loading={exportLoading}
            disabled={exportLoading || !selectedProfileId || !serverUrl}
            style={styles.button}
          >
            Export Profile
          </Button>
          <Button
            mode="outlined"
            onPress={() => { setImportDialogVisible(true); setImportError(null); setImportJson(''); }}
            disabled={!serverUrl}
            style={styles.button}
          >
            Import Profile
          </Button>

          <Divider style={styles.divider} />

          {/* Section 5: AI Configuration */}
          <Text variant="titleMedium" style={styles.sectionTitle}>AI Configuration</Text>
          <View style={styles.switchRow}>
            <Text variant="bodyMedium">Enable AI Analysis</Text>
            <Switch
              value={aiEnabled}
              onValueChange={setAiEnabled}
            />
          </View>
          <TextInput
            label="AI Server URL"
            value={aiServerUrl}
            onChangeText={setAiServerUrl}
            mode="outlined"
            keyboardType="url"
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="http://192.168.1.10:11434"
            style={styles.input}
          />
          <TextInput
            label="Model"
            value={aiModel}
            onChangeText={setAiModel}
            mode="outlined"
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="qwen2.5:0.5b"
            style={styles.input}
          />
          <Button mode="contained" onPress={saveAiConfig} style={styles.button}>
            Save AI Settings
          </Button>

          <Divider style={styles.divider} />

          {/* Section 6: Help */}
          <Text variant="titleMedium" style={styles.sectionTitle}>Help</Text>
          <Text variant="bodySmall" style={styles.helper}>
            Need a refresher on how Budgie works?
          </Text>
          <Button
            mode="outlined"
            onPress={() => setOnboardingCompleted(false)}
            style={styles.button}
          >
            Restart Tutorial
          </Button>
        </ScrollView>
      </KeyboardAvoidingView>

      <Snackbar
        visible={saved}
        onDismiss={() => setSaved(false)}
        duration={2000}
      >
        Server URL saved
      </Snackbar>

      <Snackbar
        visible={!!snackbar}
        onDismiss={() => setSnackbar('')}
        duration={2500}
      >
        {snackbar}
      </Snackbar>

      <Portal>
        <Dialog visible={importDialogVisible} onDismiss={() => setImportDialogVisible(false)}>
          <Dialog.Title>Import Profile</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodySmall" style={{ marginBottom: 8 }}>
              Paste the JSON content from a previously exported profile:
            </Text>
            {importError && (
              <Text variant="bodySmall" style={{ color: '#ef5350', marginBottom: 8 }}>
                {importError}
              </Text>
            )}
            <TextInput
              mode="outlined"
              label="Profile JSON"
              value={importJson}
              onChangeText={setImportJson}
              multiline
              numberOfLines={8}
              style={{ maxHeight: 200 }}
            />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setImportDialogVisible(false)}>Cancel</Button>
            <Button
              onPress={handleImportProfile}
              loading={importLoading}
              disabled={importLoading || !importJson.trim()}
            >
              Import
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Portal>
        <Dialog visible={deleteConfirm !== null} onDismiss={() => setDeleteConfirm(null)}>
          <Dialog.Title>Delete Profile</Dialog.Title>
          <Dialog.Content>
            <Text>
              Are you sure you want to delete "{deleteConfirm?.name}"?
              This will permanently remove all accounts, budget items, and transaction history.
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteConfirm(null)}>Cancel</Button>
            <Button textColor={theme.colors.error} onPress={() => deleteConfirm && handleDeleteProfile(deleteConfirm)}>
              Delete
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  title: { marginBottom: 24 },
  input: { marginBottom: 8 },
  helper: { marginBottom: 16, opacity: 0.7 },
  button: { marginTop: 8 },
  divider: { marginTop: 24, marginBottom: 8 },
  sectionTitle: { marginTop: 8, marginBottom: 8 },
  emptyText: { opacity: 0.7, marginTop: 8 },
  loader: { marginTop: 16 },
  errorText: { color: '#ef5350', marginTop: 8, marginBottom: 8 },
  retryButton: { marginTop: 4 },
  activeText: { marginTop: 12, opacity: 0.7 },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
});
