"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { IoMdCheckmark } from "react-icons/io";
import { Interval } from "@/lib/types/billing";
import { useSubscription } from "@/hooks/use-subscription";
import { createCheckoutSession } from "@/lib/api/billing";
import { useMetaInfo } from "@/components/context/metainfo";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { useRouter } from "next/navigation";
import { FaqSection } from "@/components/pricing/faq";

const tiers = [
  {
    name: "free",
    id: "tier-free",
    priceMonthly: "$0",
    priceYearly: "$0",
    description: "Perfect for getting started & simple projects.",
    features: [
      "1 Project",
      "10 Unique End Users",
      "1K API calls/month",
      "5 Agent Credentials",
      "1 Developer Seat",
      "Custom OAuth2 Client",
      "3 Days Log Retention",
    ],
    buttonText: "Start for Free",
    buttonVariant: "default" as const,
  },
  {
    name: "starter",
    id: "tier-starter",
    priceMonthly: "$29",
    priceYearly: "$299",
    discount: "saves $49 on annual",
    description: "For growing applications needing more capacity.",
    features: [
      "5 Projects",
      "250 Unique End Users",
      "100K API calls/month",
      "2500 Agent Credentials",
      "5 Developer Seats",
      "Custom OAuth2 Client",
      "1 Week Log Retention",
    ],
    buttonText: "Get Started",
    buttonVariant: "default" as const,
  },
  {
    name: "team",
    id: "tier-team",
    priceMonthly: "$99",
    priceYearly: "$999",
    discount: "saves $189 on annual",
    description: "Ideal for teams needing collaboration features.",
    features: [
      "10 Projects",
      "1000 Unique End Users",
      "300K API calls/month",
      "10000 Agent Credentials",
      "10 Developer Seats",
      "Custom OAuth2 Client",
      "1 Month Log Retention",
    ],
    mostPopular: true,
    buttonText: "Get Started",
    buttonVariant: "default" as const,
  },
  {
    name: "enterprise",
    id: "tier-enterprise",
    priceMonthly: "Custom",
    description: "For large-scale applications with specific needs.",
    features: [
      "Custom Projects",
      "Custom Unique End User Accounts",
      "Custom API Calls",
      "Unlimited Agent Credentials",
      "Custom Developer Seats",
      "Custom OAuth2 Client",
      "Custom Log Retention",
    ],
    buttonText: "Contact Us",
    buttonVariant: "outline" as const,
  },
];

export default function PricingPage() {
  const { data: subscription } = useSubscription();
  const { accessToken, activeOrg } = useMetaInfo();
  const [isYearly, setIsYearly] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (subscription && subscription.plan !== "free") {
      router.replace("/account");
    }
  }, [subscription, router]);

  // TODO: Enterprise button should have a mail popup
  return (
    <div className="relative bg-background text-foreground py-10 sm:py-14 min-h-screen">
      <Button
        variant="ghost"
        size="icon"
        className="absolute top-6 right-6 text-muted-foreground hover:text-foreground"
        onClick={() => router.push("/account")}
        aria-label="Close pricing page"
      >
        <X className="h-6 w-6" />
      </Button>
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <p className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">
            Pricing plans for teams of all sizes
          </p>
        </div>
        <p className="mx-auto mt-5 max-w-2xl text-center text-lg leading-8 text-muted-foreground">
          Choose an affordable plan that&apos;s packed with the best features
          for engaging your audience, creating customer loyalty, and driving
          sales.
        </p>
        <div className="flex justify-center mt-8">
          <div className="inline-flex rounded-md shadow-sm bg-muted p-1">
            <button
              onClick={() => setIsYearly(false)}
              className={`px-6 py-2 rounded-l-md text-sm font-medium focus:z-10 focus:outline-none transition-colors duration-150 ${
                !isYearly
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-background/50"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setIsYearly(true)}
              className={`px-6 py-2 rounded-r-md text-sm font-medium focus:z-10 focus:outline-none transition-colors duration-150 ${
                isYearly
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-background/50"
              }`}
            >
              Yearly
            </button>
          </div>
        </div>
        <div className="isolate mx-auto mt-14 grid grid-cols-1 gap-4 sm:mt-16 lg:mx-0 lg:max-w-none lg:grid-cols-2 xl:grid-cols-4">
          {tiers.map((tier) => (
            <Card
              key={tier.id}
              className={`flex flex-col justify-between transition-all duration-200 hover:shadow-lg hover:scale-105 ${
                tier.mostPopular ? "border-primary ring-2 ring-primary" : ""
              }`}
            >
              <CardHeader className="p-6">
                <div className="flex items-center justify-between gap-x-4">
                  <CardTitle className="text-lg">
                    {tier.name.charAt(0).toUpperCase() + tier.name.slice(1)}
                  </CardTitle>
                  {tier.mostPopular ? (
                    <Badge variant="secondary">Most popular</Badge>
                  ) : null}
                </div>
                <CardDescription className="pt-2">
                  {tier.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col justify-between p-6 pt-0">
                <div>
                  <p className="mt-0 flex items-baseline gap-x-1">
                    <span className="text-4xl font-bold tracking-tight">
                      {isYearly && tier.priceYearly
                        ? tier.priceYearly
                        : tier.priceMonthly}
                    </span>
                    {(isYearly && tier.priceYearly
                      ? tier.priceYearly
                      : tier.priceMonthly) !== "Custom" && (
                      <span className="text-sm font-semibold leading-6 text-muted-foreground">
                        /{isYearly ? "year" : "month"}
                      </span>
                    )}
                  </p>
                  {tier.discount && (
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">
                      {tier.discount}
                    </p>
                  )}
                  <ul
                    role="list"
                    className="mt-6 space-y-2.5 text-sm leading-6 text-foreground"
                  >
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex gap-x-3">
                        <IoMdCheckmark
                          className="h-6 w-5 flex-none text-primary"
                          aria-hidden="true"
                        />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
              <CardFooter className="p-6 pt-0 mt-auto">
                <Button
                  className="w-full mt-4"
                  variant={tier.buttonVariant}
                  disabled={subscription?.plan === tier.name}
                  onClick={async () => {
                    if (tier.name === "enterprise") {
                      window.location.href = "mailto:support@aipolabs.xyz";
                      return;
                    }

                    const url = await createCheckoutSession(
                      accessToken,
                      activeOrg.orgId,
                      tier.name,
                      isYearly ? Interval.Year : Interval.Month,
                    );
                    window.location.href = url;
                  }}
                >
                  {subscription?.plan === tier.name ? (
                    <div className="flex items-center gap-1">
                      <IoMdCheckmark className="text-white" />
                      Current Plan
                    </div>
                  ) : (
                    tier.buttonText
                  )}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
        <div className="mx-auto mt-8 max-w-2xl text-center">
          <p className="text-sm text-muted-foreground">
            Rate limits are set at the organization level, so every project in
            the same organization draws from the same allowance.
          </p>
        </div>
        <FaqSection />
      </div>
    </div>
  );
}
