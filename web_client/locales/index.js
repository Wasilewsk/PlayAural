export const DEFAULT_LOCALE = "en";

export const AVAILABLE_LOCALES = {
  en: "English",
  vi: "Tiếng Việt",
};

const LOADERS = {
  en: () => import("./en.js"),
  vi: () => import("./vi.js"),
};

export function normalizeLocale(locale) {
  const requested = String(locale || DEFAULT_LOCALE).trim().toLowerCase();
  if (LOADERS[requested]) {
    return requested;
  }
  const language = requested.split(/[-_]/)[0];
  return LOADERS[language] ? language : DEFAULT_LOCALE;
}

export async function loadLocaleBundle(locale) {
  const fallbackModule = await LOADERS[DEFAULT_LOCALE]();
  const fallback = fallbackModule.default || {};
  const normalized = normalizeLocale(locale);
  if (normalized === DEFAULT_LOCALE) {
    return {
      locale: DEFAULT_LOCALE,
      messages: fallback,
      fallback,
    };
  }

  try {
    const module = await LOADERS[normalized]();
    return {
      locale: normalized,
      messages: { ...fallback, ...(module.default || {}) },
      fallback,
    };
  } catch {
    return {
      locale: DEFAULT_LOCALE,
      messages: fallback,
      fallback,
    };
  }
}
