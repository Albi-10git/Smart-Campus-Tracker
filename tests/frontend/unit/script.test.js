const { describe, expect, it } = require("vitest")
const { escapeHtml, isRecentLog, sanitizePhoneNumber } = require("../../../static/js/script.js")

describe("frontend helpers", () => {
  it("sanitizes phone numbers to digits only and limits them to 10 characters", () => {
    expect(sanitizePhoneNumber("+91 98765-43210 ext 55")).toBe("9198765432")
    expect(sanitizePhoneNumber("abc")).toBe("")
  })

  it("escapes html special characters", () => {
    expect(escapeHtml(`<script>alert("x")</script>`)).toBe("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;")
  })

  it("treats recent timestamps as recent and old timestamps as stale", () => {
    const recentTimestamp = new Date(Date.now() - 60 * 1000).toISOString()
    const oldTimestamp = new Date(Date.now() - (25 * 60 * 60 * 1000)).toISOString()

    expect(isRecentLog(recentTimestamp)).toBe(true)
    expect(isRecentLog(oldTimestamp)).toBe(false)
  })
})
