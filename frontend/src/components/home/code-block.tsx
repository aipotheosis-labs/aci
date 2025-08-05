"use client";

import React from "react";
import { BiCopy } from "react-icons/bi";
import { BsCheckLg } from "react-icons/bs";
import { toast } from "sonner";

interface CodeBlockProps {
  code: string;
}

export function CodeBlock({ code }: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      toast.success("Code copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
      toast.error("Failed to copy code");
    }
  };

  return (
    <div className="bg-slate-900 dark:bg-slate-950 text-slate-300 dark:text-slate-400 p-3 rounded-md relative group overflow-auto">
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 p-2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 dark:bg-slate-900 hover:bg-slate-700 dark:hover:bg-slate-800 rounded-md"
        aria-label="Copy code"
      >
        {copied ? (
          <BsCheckLg className="h-4 w-4 text-green-500" />
        ) : (
          <BiCopy className="h-4 w-4 text-slate-300 dark:text-slate-400" />
        )}
      </button>
      <pre className="font-mono text-sm whitespace-pre pl-2 pt-2 pb-2 pr-12 overflow-x-auto">
        {code}
      </pre>
    </div>
  );
}
