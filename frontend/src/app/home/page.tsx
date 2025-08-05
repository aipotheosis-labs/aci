"use client";

import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CodeBlock } from "@/components/home/code-block";
import { BiArchiveIn } from "react-icons/bi";
import { TiDocumentText } from "react-icons/ti";

export default function HomePage() {
  return (
    <div className=" mx-auto pb-8">
      <div className="px-4 pt-4">
        <h1 className="text-2xl font-bold">Home</h1>
        <p className="text-sm text-muted-foreground">
          Start Building Awesome AI Agents In Under 5 Minutes
        </p>
      </div>
      <div className="mt-2">
        <Separator className="w-full" />
      </div>

      <div className="p-4 grid gap-6">
        <Card className="overflow-hidden">
          <CardHeader className="flex flex-row items-center bg-muted">
            <div className="mr-2 mt-1">
              <TiDocumentText />
            </div>
            <div>
              <CardTitle>Requirements</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 pt-4">
            <CardDescription>
              Please ensure you have the following:
            </CardDescription>
            <div>
              <h3 className="font-medium">Python 3.10+</h3>
            </div>
            <div>
              <h3 className="font-medium">Pip or Poetry</h3>
            </div>
            <div>
              <h3 className="font-medium inline-flex items-center gap-2">
                ACI.dev account:
                <span className="text-sm text-muted-foreground">
                  Sign up at platform.aci.dev with your sign up code
                </span>
              </h3>
            </div>
            <div>
              <h3 className="font-medium inline-flex items-center gap-2">
                An API key:
                <span className="text-sm text-muted-foreground">
                  Can be created in project settings on the ACI.dev developer
                  portal
                </span>
              </h3>
            </div>
          </CardContent>
        </Card>

        <Card className="overflow-hidden">
          <CardHeader className="flex flex-row items-center bg-muted">
            <div className="mr-2 mt-1">
              <BiArchiveIn />
            </div>
            <div>
              <CardTitle>Install and Use the Aipolabs ACI</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="mb-6">
              <h3 className="font-semibold  mb-3">
                1. Install Aipolabs ACI Python Client
              </h3>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Install With Pip:
                </p>
                <CodeBlock code="pip install aipolabs" />

                <p className="text-sm text-muted-foreground mt-2">
                  Install With Poetry:
                </p>
                <CodeBlock code="poetry add aipolabs" />
              </div>
            </div>

            <Separator className="my-6" />

            <div className="mb-6">
              <h3 className="font-semibold  mb-3">
                2. Set up your Aipolabs ACI Client
              </h3>
              <CodeBlock
                code={`from aipolabs import ACI

aci = ACI()

LINKED_ACCOUNT_OWNER_ID = os.getenv("LINKED_ACCOUNT_OWNER_ID", "")
if not LINKED_ACCOUNT_OWNER_ID:
    raise ValueError("LINKED_ACCOUNT_OWNER_ID is not set")`}
              />
            </div>

            <Separator className="my-6" />

            <div className="mb-6">
              <h3 className="font-semibold  mb-3">
                3. Add a Tool to Your LLM Request
              </h3>
              <CodeBlock
                code={`function_definition = aci.functions.get_definition("BRAVE_SEARCH__WEB_SEARCH")

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to a variety of tools."},
        {"role": "user", "content": "What is aipolabs ACI?"}
    ],
    tools=[function_definition],
    tool_choice="Required"
)`}
              />
            </div>

            <Separator className="my-6" />

            <div>
              <h3 className="font-semibold  mb-3">4. Execute Tool Calls</h3>
              <CodeBlock
                code={`tool_call = (
    response.choices[0].message.tool_calls[0]
    if response.choices[0].message.tool_calls
    else None
)

result = aci.functions.execute(
    tool_call.function.name,
    json.loads(tool_call.function.arguments),
    linked_account_owner_id=LINKED_ACCOUNT_OWNER_ID
)
print(f"function call result: {result}")`}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
