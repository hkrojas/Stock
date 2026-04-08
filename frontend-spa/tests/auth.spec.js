import { test, expect } from "@playwright/test"
import { login } from "./helpers/auth"

test.describe("Authentication Flow", () => {
  test("should login successfully as superadmin", async ({ page }) => {
    // These credentials are based on backend/scripts/seed_db.py
    await login(page, "superboss", "password123")
    
    // Verify dashboard access
    await expect(page).toHaveURL(/.*dashboard/)
    await expect(page.getByText("CEO")).toBeVisible()
  })

  test("should show error on invalid credentials", async ({ page }) => {
    await page.goto("/login")
    await page.getByTestId("login-username").fill("wronguser")
    await page.getByTestId("login-password").fill("wrongpass")
    await page.getByTestId("login-submit").click()
    
    // Check for error message (based on LoginView.vue error div)
    await expect(page.locator(".border-rose-500\\/20")).toBeVisible()
  })
})
