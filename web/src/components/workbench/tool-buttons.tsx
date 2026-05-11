"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Languages, ChevronDown, ShieldCheck, Loader2 } from "lucide-react";
import { SUPPORTED_LANGUAGES, type LanguageCode } from "@/lib/types/workbench";

interface ToolButtonsProps {
  onTranslate?: (targetLanguage: LanguageCode) => void;
  isTranslating?: boolean;
  onFactCheck?: () => void;
  isFactChecking?: boolean;
}

export function ToolButtons({ onTranslate, isTranslating, onFactCheck, isFactChecking }: ToolButtonsProps) {
  const [selectedLang, setSelectedLang] = useState<LanguageCode>("en");
  const [showLangPicker, setShowLangPicker] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showLangPicker) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setShowLangPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showLangPicker]);

  const handleTranslateClick = () => {
    if (!onTranslate) return;
    onTranslate(selectedLang);
    setShowLangPicker(false);
  };

  return (
    <div className="flex items-center gap-2 p-3 bg-card rounded-md shadow-card">
      {/* Translate button with language picker */}
      <div className="relative flex items-center gap-1" ref={pickerRef}>
        <Button
          variant="outline"
          size="sm"
          disabled={!onTranslate || isTranslating}
          onClick={handleTranslateClick}
          className="text-xs border-outline-variant/40 text-muted-foreground hover:text-foreground hover:border-brand/30"
        >
          {isTranslating ? (
            <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
          ) : (
            <Languages className="h-3.5 w-3.5 mr-1" />
          )}
          {isTranslating ? "翻译中..." : "一键翻译"}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowLangPicker(!showLangPicker)}
          className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground border-outline-variant/40 hover:border-brand/30"
          disabled={!onTranslate || isTranslating}
        >
          {SUPPORTED_LANGUAGES.find((l) => l.code === selectedLang)?.label ?? "英文"}
          <ChevronDown className="h-3 w-3 ml-0.5 opacity-60" />
        </Button>
        {showLangPicker && (
          <div className="absolute top-full left-0 mt-1 z-10 bg-card border border-outline-variant/30 rounded-md shadow-card py-1 min-w-[120px]">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  setSelectedLang(lang.code);
                  setShowLangPicker(false);
                }}
                className={`w-full px-3 py-1.5 text-left text-xs hover:bg-accent transition-colors flex items-center justify-between ${
                  selectedLang === lang.code ? "text-brand font-medium bg-brand/5" : "text-muted-foreground"
                }`}
              >
                <span>{lang.label}</span>
                <span className={`ml-2 font-mono text-[10px] ${selectedLang === lang.code ? "text-brand/70" : "text-muted-foreground/50"}`}>
                  {lang.code}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={onFactCheck}
        disabled={!onFactCheck || isFactChecking}
        className="text-xs border-outline-variant/40 text-muted-foreground hover:text-foreground hover:border-brand/30"
      >
        {isFactChecking ? (
          <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
        ) : (
          <ShieldCheck className="h-3.5 w-3.5 mr-1" />
        )}
        {isFactChecking ? "核查中..." : "事实核查"}
      </Button>
    </div>
  );
}