import * as React from 'react';
import {
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    CircularProgress,
    Typography,
} from '@mui/material';
import { api } from './renderUtils';

function renderMarkdown(md: string): string {
    let html = md
        // Escape HTML
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Headers
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        // Bold and italic
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Bullet lists
        .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
        // Numbered lists
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Horizontal rules
        .replace(/^---$/gm, '<hr/>')
        // Line breaks (double newline = paragraph)
        .replace(/\n\n/g, '</p><p>')
        // Single newlines within paragraphs
        .replace(/\n/g, '<br/>');

    // Wrap consecutive <li> tags in <ul>
    html = html.replace(/((?:<li>.*?<\/li><br\/>?)+)/g, (match) => {
        const cleaned = match.replace(/<br\/?>/g, '');
        return `<ul>${cleaned}</ul>`;
    });

    return `<p>${html}</p>`;
}

export default function CalendarAIAnalysis({ open, close, profileId }: { open: boolean, close: () => void, profileId: number }) {
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState<string | null>(null);
    const [error, setError] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (open && profileId) {
            setLoading(true);
            setResult(null);
            setError(null);
            api.post(`/ai/analyze/${profileId}`, {})
                .then((data: any) => {
                    if (data.error) {
                        setError(data.error);
                    } else {
                        setResult(data.analysis);
                    }
                })
                .catch((e: any) => setError(e.message))
                .finally(() => setLoading(false));
        }
    }, [open, profileId]);

    return (
        <Dialog open={open} onClose={close} maxWidth="md" fullWidth>
            <DialogTitle>AI Budget Analysis</DialogTitle>
            <DialogContent>
                {loading && (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <CircularProgress />
                        <Typography style={{ marginTop: '16px' }}>
                            Analyzing your budget...
                        </Typography>
                    </div>
                )}
                {error && (
                    <Typography color="error" style={{ whiteSpace: 'pre-wrap' }}>
                        {error}
                    </Typography>
                )}
                {result && (
                    <div
                        style={{ lineHeight: 1.7, fontSize: '14px' }}
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(result) }}
                    />
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={close}>Close</Button>
            </DialogActions>
        </Dialog>
    );
}
