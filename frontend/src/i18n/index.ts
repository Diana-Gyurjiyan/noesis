import en from "./en";
import nl from "./nl";
import type { Language } from "../types";

export type Translation = { [Key in keyof typeof en]: string };

export const translations: Record<Language, Translation> = { en, nl };
