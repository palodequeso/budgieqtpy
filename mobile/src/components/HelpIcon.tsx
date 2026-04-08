import React, { useState } from 'react';
import { IconButton, Dialog, Portal, Button, Text } from 'react-native-paper';

interface HelpIconProps {
  text: string;
}

export default function HelpIcon({ text }: HelpIconProps) {
  const [visible, setVisible] = useState(false);

  return (
    <>
      <IconButton icon="help-circle-outline" size={20} onPress={() => setVisible(true)} />
      <Portal>
        <Dialog visible={visible} onDismiss={() => setVisible(false)}>
          <Dialog.Content>
            <Text variant="bodyMedium">{text}</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setVisible(false)}>OK</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </>
  );
}
