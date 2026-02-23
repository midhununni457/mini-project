"use client";

import { useState } from "react";
import Particles from "./components/Particles"; 

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setMessage("");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first.");
      return;
    }

    setIsLoading(true);
    setMessage("");

    const formData = new FormData();
    formData.append("apk", file);

    try {
      const response = await fetch("http://localhost:3000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setMessage("File uploaded successfully!");
        setFile(null);
      } else {
        setMessage("Upload failed. Please try again.");
      }
    } catch (error) {
      console.error(error);
      setMessage("An error occurred while uploading.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden bg-zinc-50 dark:bg-black font-sans">
      
      <Particles
        className="absolute inset-0"
        particleCount={100}
        particleColors={["#333333", "#555555"]} 
        speed={0.2}
      />

      <main className="relative z-10 flex w-full max-w-2xl flex-col items-center px-4 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-black dark:text-zinc-50 mb-6">
          RansomSentry
        </h1>

        <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-10 max-w-lg">
          Upload your APKs below to detect potential ransomware threats.
        </p>

        <div className="w-full max-w-md p-8 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm rounded-2xl shadow-xl border border-zinc-200 dark:border-zinc-800">
          <div className="flex flex-col gap-4">
            <label className="block">
              <span className="sr-only">Choose file</span>
              <input
                type="file"
                accept=".apk"
                onChange={handleFileChange}
                className="block w-full text-sm text-zinc-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-zinc-100 file:text-zinc-700 hover:file:bg-zinc-200 dark:file:bg-zinc-800 dark:file:text-zinc-300 dark:hover:file:bg-zinc-700 cursor-pointer"
              />
            </label>

            <button
              onClick={handleUpload}
              disabled={isLoading || !file}
              className="w-full rounded-full bg-foreground text-background py-3 font-medium transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Uploading..." : "Analyze File"}
            </button>

            {message && (
              <p
                className={`text-sm font-medium ${
                  message.includes("success") ? "text-green-600" : "text-red-500"
                }`}
              >
                {message}
              </p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}