import axios from 'axios';
import { MessageInterface } from '@/types/types';
import { API_KEY, API_URL } from '@/config/runpodConfigs';

const BASE_URL = API_URL ? API_URL.replace(/\/chat$/, '') : '';
const STREAM_URL = BASE_URL ? `${BASE_URL}/chat/stream` : '';
const SESSION_URL = BASE_URL ? `${BASE_URL}/session` : '';

function getSessionId(): string {
    try {
        const key = 'cafeai_session_id';
        const stored = localStorage.getItem(key);
        if (stored) return stored;
        const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem(key, id);
        return id;
    } catch {
        return 'default';
    }
}

async function loadSession(): Promise<MessageInterface[]> {
    if (!SESSION_URL) return [];
    try {
        const id = getSessionId();
        const resp = await fetch(`${SESSION_URL}/${id}`);
        if (!resp.ok) return [];
        const data = await resp.json();
        return Array.isArray(data.messages) ? data.messages : [];
    } catch {
        return [];
    }
}

async function clearSession(): Promise<void> {
    if (!SESSION_URL) return;
    try {
        const id = getSessionId();
        await fetch(`${SESSION_URL}/${id}`, { method: 'DELETE' });
    } catch {
        // best-effort
    }
}

async function callChatBotAPI(messages: MessageInterface[]): Promise<MessageInterface> {
    try {
        const response = await axios.post(API_URL, {
            input: { messages }
        }, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            }
        });

        let output = response.data;
        let outputMessage: MessageInterface = output['output'];

        return outputMessage;
    } catch (error) {
        console.error('Error calling the API:', error);
        throw error;
    }
}

type StreamEvent =
    | { type: 'token'; delta: string }
    | { type: 'done'; memory: any }
    | { type: 'error'; message: string };

async function* callChatBotStreamAPI(messages: MessageInterface[], sessionId?: string): AsyncGenerator<StreamEvent> {
    const sid = sessionId ?? getSessionId();
    const response = await fetch(STREAM_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEY}`,
            'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ input: { messages }, session_id: sid }),
    });

    if (!response.ok) {
        throw new Error(`Stream request failed: ${response.status}`);
    }

    if (!response.body) {
        throw new Error('No response body for streaming');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const raw = line.slice(6).trim();
                if (!raw) continue;
                try {
                    yield JSON.parse(raw) as StreamEvent;
                } catch {
                    // malformed SSE chunk — skip
                }
            }
        }
    }
}

export { callChatBotAPI, callChatBotStreamAPI, loadSession, clearSession, getSessionId };