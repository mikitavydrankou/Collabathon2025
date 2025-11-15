const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  username: string;
  name: string;
  surname: string;
}

export interface UserResponse {
  user_id: number;
  username: string;
  name: string;
  surname: string;
  balance: number;
  bank_number: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    return response.json();
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await fetch(`${this.baseUrl}/auth/me`, {
      method: "GET",
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch user data");
    }

    return response.json();
  }

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_data");
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem("access_token");
  }

  getStoredUserData(): LoginResponse | null {
    const userData = localStorage.getItem("user_data");
    return userData ? JSON.parse(userData) : null;
  }

  async startChatbot(userId: number): Promise<{
    session_id: string;
    message: string;
    buttons: string[];
    button_helper_text?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/chatbot/start`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ user_id: userId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to start chatbot");
    }

    return response.json();
  }

  async sendChatbotMessage(data: {
    session_id?: string;
    user_id: number;
    message?: string;
    action?: string;
  }): Promise<{
    session_id: string;
    stage: string;
    message: string;
    buttons?: string[];
    button_helper_text?: string;
    suggestion?: any;
    transaction_data?: any;
    show_confirm_payment: boolean;
    validation_problems?: string[];
  }> {
    const response = await fetch(`${this.baseUrl}/chatbot/message`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  }

  async transcribeAudio(audioBlob: Blob): Promise<{
    text: string;
    success: boolean;
  }> {
    const formData = new FormData();
    formData.append("audio", audioBlob, "audio.webm");

    const token = localStorage.getItem("access_token");
    const response = await fetch(`${this.baseUrl}/chatbot/transcribe`, {
      method: "POST",
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to transcribe audio");
    }

    return response.json();
  }

  async extractTextFromImage(imageBlob: Blob): Promise<{
    text: string;
    success: boolean;
    message?: string;
  }> {
    const formData = new FormData();
    formData.append("image", imageBlob, "image.jpg");

    const token = localStorage.getItem("access_token");
    const response = await fetch(`${this.baseUrl}/chatbot/ocr`, {
      method: "POST",
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to extract text from image");
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
