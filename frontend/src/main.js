import { jsx as _jsx } from "react/jsx-runtime";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import "./style.css";
createRoot(document.getElementById("root")).render(_jsx(BrowserRouter, { children: _jsx(App, {}) }));

