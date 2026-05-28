import { create } from "zustand";
import { persist } from "zustand/middleware";

export type User = { id: number; email: string; username: string };

type State = {
  token: string | null;
  user: User | null;
  setSession: (token: string, user: User) => void;
  logout: () => void;
};

export const useAuthStore = create<State>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "ai-research-agent-auth" }
  )
);
