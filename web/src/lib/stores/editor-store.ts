"use client";

import { create } from "zustand";

interface EditorState {
  content: string;
  wordCount: number;
  targetWordCount: number;
  completionPercent: number;
  setContent: (content: string) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  content: "",
  wordCount: 0,
  targetWordCount: 1600,
  completionPercent: 0,
  setContent: (content) => {
    const wordCount = content.replace(/\s+/g, "").length;
    set({
      content,
      wordCount,
      completionPercent: Math.round((wordCount / 1600) * 100),
    });
  },
}));