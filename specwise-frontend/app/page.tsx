import { FileUpload } from "@/components/file-upload";
import { TasksTable } from "@/components/tasks-table";

import { TasksInitializer } from "@/components/tasks-initializer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FilesTable } from "@/components/file_table";

export default function Home() {
  return (
    <div className="space-y-8">
      <TasksInitializer />
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">SPECWISE File Processor</h1>
        <p className="text-muted-foreground">
          Upload files for processing and view task status
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <FileUpload />
        </div>
        <div className="md:col-span-2">
          <Tabs defaultValue="tasks" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="tasks">Processing Tasks</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
            </TabsList>
            <TabsContent value="tasks" className="mt-6">
              <TasksTable />
            </TabsContent>
            <TabsContent value="files" className="mt-6">
              <FilesTable />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
