import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

// On remplace le client HTTP : aucune requête réseau, et axios (ESM) n'est pas chargé par Jest
jest.mock("./api", () => ({
  api: {
    get: jest.fn(() => Promise.reject({ response: { status: 401 } })),
    post: jest.fn(),
  },
  errorMessage: (e) => e?.message || "error",
  streamGenerate: jest.fn(),
  API_URL: "http://test",
}));

test("shows the login form when there is no valid session", async () => {
  render(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: /login/i })).toBeInTheDocument());
  expect(screen.getByPlaceholderText(/username/i)).toBeInTheDocument();
});

test("switches to the register form", async () => {
  render(<App />);
  const switchBtn = await screen.findByRole("button", { name: /^register$/i });
  switchBtn.click();
  expect(await screen.findByPlaceholderText(/confirm password/i)).toBeInTheDocument();
});
