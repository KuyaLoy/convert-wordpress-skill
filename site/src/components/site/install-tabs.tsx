"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/8bit/tabs";
import { CodeLine } from "@/components/site/copy-button";

type Agent = { id: string; label: string; folder: string };

export function InstallTabs({ agents, repo }: { agents: Agent[]; repo: string }) {
  return (
    <Tabs defaultValue={agents[0].id} font="normal" className="gap-6">
      <TabsList
        aria-label="Your AI agent"
        className="mx-1.5 flex h-auto! w-[calc(100%-12px)] flex-wrap justify-start gap-1 p-1.5"
      >
        {agents.map((a) => (
          <TabsTrigger
            key={a.id}
            value={a.id}
            className="h-auto! flex-none px-3 py-2 font-pixel text-base data-[state=active]:bg-primary! data-[state=active]:text-primary-foreground!"
          >
            {a.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {agents.map((a) => (
        <TabsContent key={a.id} value={a.id} className="text-base">
          <p className="mb-3 text-muted-foreground">
            Skills folder: <code className="text-foreground">{a.folder}</code>
          </p>
          <CodeLine text={`git clone ${repo} ${a.folder}`} />
        </TabsContent>
      ))}
    </Tabs>
  );
}
