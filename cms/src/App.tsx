import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { api, getToken } from "./api/client";
import { ErrorBox, Layout, Loading } from "./components/Layout";
import Login from "./pages/Login";
import Publish from "./pages/Publish";
import ShowEdit from "./pages/ShowEdit";
import Shows from "./pages/Shows";

const qc = new QueryClient();

function Shell() {
  const token = getToken();
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, enabled: !!token, retry: false });
  if (!token) return <Navigate to="/login" replace />;
  if (me.isLoading) return <Loading />;
  if (me.isError) {
    return (
      <div className="page">
        <ErrorBox error={me.error} />
        <a href="/login">Sign in</a>
      </div>
    );
  }
  return (
    <Layout email={me.data!.email} role={me.data!.role}>
      <Routes>
        <Route path="/" element={<Shows />} />
        <Route path="/shows/new" element={<ShowEdit />} />
        <Route path="/shows/:id" element={<ShowEdit />} />
        <Route path="/publish" element={<Publish />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Shell />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
