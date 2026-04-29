import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import Editor from "./pages/Editor";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        path: "/",
        element: <Dashboard />,
        index: true,
      },
      {
        path: "/dashboard",
        element: <Dashboard />,
      },
      {
        path: "/projects",
        element: <Projects />,
      },
      {
        path: "/projects/:projectId",
        element: <ProjectDetail />,
      },
      {
        path: "/projects/:projectId/chapters/:chapterId/edit",
        element: <Editor />,
      },
      {
        path: "/projects/:projectId/editor",
        element: <Editor />,
      },
    ],
  },
]);

export default router;