import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Dialog, Portal, Button, Text, useTheme } from 'react-native-paper';

const STEPS = [
  {
    title: 'Welcome to Budgie',
    body: "Budgie helps you plan your finances by scheduling bills and income onto a calendar. Here's how to get started.",
  },
  {
    title: 'Create a Profile',
    body: 'Profiles keep budgets separate — one for yourself, one shared with a partner, etc. You can create more anytime from Settings.',
  },
  {
    title: 'Add Your Accounts',
    body: 'Head to the Accounts tab and add your bank accounts (checking, savings, credit cards). These track where your money flows.',
  },
  {
    title: 'Set Up Your Budget',
    body: "In the Budget tab, add your recurring income and expenses. Each item has a schedule — 'monthly on the 1st', 'biweekly on Friday', etc.",
  },
  {
    title: 'Run Extrapolation',
    body: "Go to the Calendar tab and tap Extrapolate. This projects your budget items into the future so you can see what's coming.",
  },
  {
    title: "You're Ready!",
    body: 'The calendar is your main workspace. Mark items as paid, add one-off expenses, compute savings, and hide past pay periods as you go.',
  },
];

interface OnboardingDialogProps {
  visible: boolean;
  onComplete: () => void;
}

export default function OnboardingDialog({ visible, onComplete }: OnboardingDialogProps) {
  const [step, setStep] = useState(0);
  const theme = useTheme();

  const isLast = step === STEPS.length - 1;

  const finish = () => {
    setStep(0);
    onComplete();
  };

  return (
    <Portal>
      <Dialog visible={visible} onDismiss={finish}>
        <Dialog.Content>
          {/* Step dots */}
          <View style={styles.dotsRow}>
            {STEPS.map((_, i) => (
              <View
                key={i}
                style={[
                  styles.dot,
                  {
                    backgroundColor:
                      i === step ? theme.colors.primary : theme.colors.surfaceDisabled,
                  },
                ]}
              />
            ))}
          </View>

          <Text variant="headlineSmall" style={styles.title}>
            {STEPS[step].title}
          </Text>

          <Text variant="bodyMedium" style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
            {STEPS[step].body}
          </Text>
        </Dialog.Content>

        <Dialog.Actions style={styles.actions}>
          {step > 0 ? (
            <Button onPress={() => setStep((s) => s - 1)}>Back</Button>
          ) : (
            <View style={styles.placeholder} />
          )}

          <View style={styles.rightActions}>
            <Button onPress={finish} textColor={theme.colors.onSurfaceVariant}>
              Skip
            </Button>
            <Button
              mode="contained"
              onPress={isLast ? finish : () => setStep((s) => s + 1)}
            >
              {isLast ? 'Get Started' : 'Next'}
            </Button>
          </View>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
}

const styles = StyleSheet.create({
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 20,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  title: {
    textAlign: 'center',
    fontWeight: 'bold',
    marginBottom: 12,
  },
  body: {
    textAlign: 'center',
    lineHeight: 24,
  },
  actions: {
    justifyContent: 'space-between',
    paddingHorizontal: 8,
  },
  rightActions: {
    flexDirection: 'row',
    gap: 4,
  },
  placeholder: {
    width: 60,
  },
});
