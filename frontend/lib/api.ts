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
}

export const apiClient = new ApiClient();
