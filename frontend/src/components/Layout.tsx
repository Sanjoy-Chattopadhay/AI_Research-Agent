import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  MessageSquare,
  History as HistoryIcon,
  FileText,
  BarChart3,
  LogOut,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/store/auth";

const nav = [
  { to: "/chat", icon: MessageSquare, label: "Chat" },
  { to: "/history", icon: HistoryIcon, label: "History" },
  { to: "/documents", icon: FileText, label: "Documents" },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
];

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-slate-950">
      <aside className="w-60 shrink-0 border-r border-slate-800 bg-slate-950/60 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-800 flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-500 to-cyan-500 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Research Agent</div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">v3 · multi-agent</div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 p-3 space-y-2">
          <div className="px-2 text-xs text-slate-500 truncate">
            {user?.username} <span className="text-slate-600">· {user?.email}</span>
          </div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="btn-ghost w-full justify-start"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
