import { test, expect } from "@playwright/test"
import { login } from "./helpers/auth"

test.describe("Orders Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Admin login (admin_juan)
    await login(page, "admin_juan", "password123")
  })

  test("should view order history", async ({ page }) => {
    await page.goto("/orders/history")
    
    // Breadcrumbs or title
    await expect(page.getByText("Historial Operativo")).toBeVisible()
    
    // Check if table is present
    const table = page.locator("table")
    await expect(table).toBeVisible()
  })

  test("should navigate to new order view", async ({ page }) => {
    await page.goto("/orders/new")
    await expect(page.getByText("Nueva Orden")).toBeVisible()
    await expect(page.getByText("Seleccionar Edificio")).toBeVisible()
  })
})
