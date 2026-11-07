import React from "react";
import ReactDOM from "react-dom/client";
import { MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { createTheme } from "@mantine/core";
import App from "./App";

import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MantineProvider
      defaultColorScheme="light"
      theme={createTheme({
        primaryColor: "lime",
      })}
    >
      <Notifications position="top-right" />
      <App />
    </MantineProvider>
  </React.StrictMode>,
);
