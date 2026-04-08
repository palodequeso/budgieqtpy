import * as React from 'react';
import { IconButton, Tooltip } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

export default function HelpIcon({ text }: { text: string }) {
    return (
        <Tooltip title={text} arrow>
            <IconButton size="small" sx={{ ml: 0.5, opacity: 0.6 }}>
                <HelpOutlineIcon fontSize="small" />
            </IconButton>
        </Tooltip>
    );
}
