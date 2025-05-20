import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

const faqs = [
  {
    value: "faq-1",
    question: "Can I upgrade my plan at any time?",
    answer:
      "Yes, you can upgrade your plan at any time. Stripe will automatically charge for pro-rata pricing differences during upgrades.",
  },
  {
    value: "faq-2",
    question:
      "What happens if I exceed the unique end user and/or the API call limits?",
    answer:
      "You will have to upgrade your plan to continue using the managed service if you exceed the unique end user count and/or the API call limits.",
  },
  {
    value: "faq-3",
    question: "What are unique end users?",
    answer: (
      <>
        <a
          href="https://platform.aci.dev/linked-accounts"
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          ACI.dev
        </a>{" "}
        allows developers to manage their own end users&apos; authentication to
        various applications on the ACI.dev platform. So each unique user
        connecting an account to some application on the platform is counted as
        a unique end user. Each unique end user might link multiple accounts
        (e.g. a linked account with Gmail, a linked account with Notion, a
        linked account with Figma, all belonging to a single unique end user).
      </>
    ),
  },
  {
    value: "faq-4",
    question: "What are agent credentials?",
    answer:
      "The ACI Agent Secrets Manager application allows AI agents to store and retrieve secrets to enhance agent reliability and autonomy. It’s especially useful for web agents that need to interact with login pages.",
  },
  {
    value: "faq-5",
    question: "What are custom OAuth2 clients?",
    answer:
      "Custom OAuth2 clients are specific applications you’ve registered with an authorization server (e.g., Google or a third-party platform) to access protected resources on behalf of your users. For example, they let your end users sign into Google through your own OAuth2 client rather than ACI.dev’s default client.",
  },
  {
    value: "faq-6",
    question: "Can I cancel my subscription?",
    answer:
      "Yes, you can cancel your subscription at any time. The cancellation will take effect at the end of your current billing cycle.",
  },
  {
    value: "faq-7",
    question:
      "What happens to my users’ linked accounts if I cancel or downgrade my subscription?",
    answer:
      "Your users can continue using their linked accounts until the end of the billing period. If your unique end user count exceeds the allowance for the tier you downgrade to, they will be locked out until you reduce your end user count or upgrade again. You can also contact us to export linked-account data.",
  },
  {
    value: "faq-8",
    question: "What is your refund policy?",
    answer:
      "Subscriptions are non-refundable for their duration. However, if you’re a consumer in the UK or EU, you have a 14-day “Cooling Off Period” from purchase date to cancel without reason and receive a prorated refund from the cancellation date through the end of the paid period.",
  },
];

export function FaqSection() {
  return (
    <div className="mx-auto max-w-2xl px-6 lg:px-8 mt-16">
      <h2 className="text-3xl font-bold text-center">
        Frequently Asked Questions
      </h2>
      <Accordion type="single" collapsible className="mt-6 space-y-2">
        {faqs.map(({ value, question, answer }) => (
          <AccordionItem key={value} value={value}>
            <AccordionTrigger>{question}</AccordionTrigger>
            <AccordionContent>{answer}</AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
