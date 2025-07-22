class API {
    private _baseUrl: string;
    private _headers: HeadersInit;

    constructor(baseUrl: string) {
        this._baseUrl = baseUrl;
        this._headers = {
            'Content-Type': 'application/json',
        };
    }

    public get sessionId(): string | null {
        return localStorage.getItem('budgie:profileId');
    }

    private async _handleRequest(
        url: string,
        method: string,
        body?: any,
    ): Promise<Response> {
        const result = await fetch(`${this._baseUrl}${url}`, {
            method,
            headers: this._headers,
            body: JSON.stringify(body),
        });
        return result.json();
    }

    public async get(url: string): Promise<any> {
        return this._handleRequest(url, 'GET');
    }

    public async post(url: string, body: any): Promise<any> {
        return this._handleRequest(url, 'POST', body);
    }

    public async put(url: string, body: any): Promise<any> {
        return this._handleRequest(url, 'PUT', body);
    }

    public async delete(url: string): Promise<any> {
        return this._handleRequest(url, 'DELETE');
    }
}

export const api = new API('');

export function showSaveDialog(): Promise<{ filePath: string, cancelled: boolean, }> {
    return (window as any).dialog.open('showSaveDialog');
}
