import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { Toaster } from "sonner"

import { AppLayout } from "./components/layout/AppLayout"
import { LoginPage } from "./pages/LoginPage"
import { ProjectsPage } from "./pages/ProjectsPage"
import { ProjectDetailPage } from "./pages/ProjectDetailPage"
import { TestCasePage } from "./pages/TestCasePage"
import { TestPlansPage } from "./pages/TestPlansPage"
import { ExecutionsPage } from "./pages/ExecutionsPage"
import { ExecutionDetailPage } from "./pages/ExecutionDetailPage"
import { ExecutionRunPage } from "./pages/ExecutionRunPage"
import { NewExecutionPage } from "./pages/NewExecutionPage"
import { UsersPage } from "./pages/UsersPage"
import { ProfilePage } from "./pages/ProfilePage"
import { MembersPage } from "./pages/MembersPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
    mutations: {
      onError: (err) => {
        const msg = err?.response?.data?.detail ?? "Something went wrong"
        import("sonner").then(({ toast }) => toast.error(msg))
      },
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/projects" replace />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
            <Route path="/projects/:id/plans" element={<TestPlansPage />} />
            <Route path="/projects/:id/executions" element={<ExecutionsPage />} />
            <Route path="/projects/:id/executions/new" element={<NewExecutionPage />} />
            <Route path="/projects/:id/members" element={<MembersPage />} />
            <Route path="/cases/:id" element={<TestCasePage />} />
            <Route path="/executions/:id" element={<ExecutionDetailPage />} />
            <Route path="/executions/:id/run" element={<ExecutionRunPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
