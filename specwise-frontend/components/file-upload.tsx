"use client";

import type React from "react";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Upload, File, X } from "lucide-react";
import { useUploadData } from "@/hooks/use-data";
import { useTasksStore } from "@/store/tasks-store";
import { toast } from "@/components/ui/use-toast";
import { Progress } from "@/components/ui/progress";

export function FileUpload() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadData();
  const { addTasks } = useTasksStore();
  const [customerId, setCustomerId] = useState<string>(""); // New state for customer ID

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select at least one file to upload.",
        variant: "destructive",
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("customer_id", customerId);
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + 5;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 300);

      const response = await uploadMutation.mutateAsync(formData);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (Array.isArray(response)) {
        addTasks(response);

        toast({
          title: "Upload successful",
          description: `${files.length} file(s) uploaded successfully.`,
        });

        setFiles([]);
      } else {
        throw new Error("Invalid response format");
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description:
          "There was an error uploading your files. Please try again.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Upload Files</CardTitle>
        <CardDescription>
          Upload files for processing. Supported formats: PDF, Excel, CSV.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <label className="text-sm font-medium">Customer ID</label>
          <input
            type="text"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            className="mt-1 w-full bg-white border border-gray-300 rounded-md p-2"
            disabled={uploading}
          />
        </div>
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            files.length > 0
              ? "border-gray-300"
              : "border-gray-200 hover:border-gray-300"
          } transition-colors cursor-pointer`}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            className="hidden"
            disabled={uploading}
          />
          <Upload className="h-10 w-10 mx-auto text-gray-400 mb-2" />
          <p className="text-sm font-medium">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Maximum file size: 10MB
          </p>
        </div>

        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium">
              Selected Files ({files.length})
            </div>
            <div className="max-h-40 overflow-y-auto space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-muted p-2 rounded-md"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <File className="h-4 w-4 text-blue-500" />
                    <span className="text-sm truncate">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(0)} KB
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    disabled={uploading}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {uploadProgress > 0 && (
          <div className="mt-4 space-y-1">
            <div className="flex justify-between text-xs">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-1.5" />
          </div>
        )}

        <Button
          className="w-full mt-4"
          onClick={handleUpload}
          disabled={files.length === 0 || uploading || !customerId}
        >
          {uploading ? "Uploading..." : "Upload Files"}
        </Button>
      </CardContent>
    </Card>
  );
}
