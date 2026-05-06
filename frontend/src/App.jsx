import { lazy, Suspense } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "sonner"

import { AppLayout } from "./components/layout/AppLayout"

const LoginPage = lazy(() => import("./pages/LoginPage").then(m => ({ default: m.LoginPage })))
const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then(m => ({ default: m.ProjectsPage })))
const ProjectDetailPage = lazy(() => import("./pages/ProjectDetailPage").then(m => ({ default: m.ProjectDetailPage })))
const TestCasePage = lazy(() => import("./pages/TestCasePage").then(m => ({ default: m.TestCasePage })))
const TestPlansPage = lazy(() => import("./pages/TestPlansPage").then(m => ({ default: m.TestPlansPage })))
const PlanDetailPage = lazy(() => import("./pages/PlanDetailPage").then(m => ({ default: m.PlanDetailPage })))
const ExecutionsPage = lazy(() => import("./pages/ExecutionsPage").then(m => ({ default: m.ExecutionsPage })))
const ExecutionDetailPage = lazy(() => import("./pages/ExecutionDetailPage").then(m => ({ default: m.ExecutionDetailPage })))
const ExecutionRunPage = lazy(() => import("./pages/ExecutionRunPage").then(m => ({ default: m.ExecutionRunPage })))
const NewExecutionPage = lazy(() => import("./pages/NewExecutionPage").then(m => ({ default: m.NewExecutionPage })))
const UsersPage = lazy(() => import("./pages/UsersPage").then(m => ({ default: m.UsersPage })))
const ProfilePage = lazy(() => import("./pages/ProfilePage").then(m => ({ default: m.ProfilePage })))
const MembersPage = lazy(() => import("./pages/MembersPage").then(m => ({ default: m.MembersPage })))

let DevTools = () => null
if (import.meta.env.DEV) {
  DevTools = lazy(() =>
    import("@tanstack/react-query-devtools").then(m => ({ default: m.ReactQueryDevtools }))
  )
}

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
        <Suspense fallback={null}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<AppLayout />}>
              <Route index element={<Navigate to="/projects" replace />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/:id" element={<ProjectDetailPage />} />
              <Route path="/projects/:id/plans" element={<TestPlansPage />} />
              <Route path="/plans/:id" element={<PlanDetailPage />} />
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
        </Suspense>
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
      <Suspense fallback={null}>
        <DevTools initialIsOpen={false} />
      </Suspense>
    </QueryClientProvider>
  )
}
