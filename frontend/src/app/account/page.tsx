"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { createCustomerPortalSession } from "@/lib/api/billing";
import { useSubscription } from "@/hooks/use-subscription";
import { useLogoutFunction } from "@propelauth/react";
import Link from "next/link";
import { BsStars } from "react-icons/bs";
import { RiUserSettingsLine } from "react-icons/ri";

export default function AccountPage() {
  const { user, activeOrg, accessToken } = useMetaInfo();
  const logoutFn = useLogoutFunction();

  const { data: subscription, isLoading } = useSubscription();

  return (
    <div>
      <div className="mx-4 py-6">
        <h1 className="text-2xl font-semibold">Account Settings</h1>
      </div>

      <Separator />

      <div className="container p-4 space-y-4">
        {/* User Details Section */}
        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">User Name</label>
          </div>
          <div className="flex items-center px-2">{`${user.firstName} ${user.lastName}`}</div>
        </div>

        <Separator />

        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Email</label>
          </div>
          <div className="flex items-center px-2">{user.email}</div>
        </div>

        <Separator />

        {/* <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Password</label>
            <p className="text-sm text-muted-foreground">
              Here is your password
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Input
              type="password"
              defaultValue="************"
              className="w-96"
              readOnly
            />
            <Button variant="outline">Reset</Button>
          </div>
        </div>

        <Separator /> */}

        {/* Past Invoices Section */}
        {/* <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Past Invoices</label>
            <p className="text-sm text-muted-foreground">
              Here are all your invoices
            </p>
          </div>
          <div className="flex-1 space-y-2">
            {[
              { id: 3, date: "2024-04-23" },
              { id: 2, date: "2024-04-23" },
              { id: 1, date: "2024-04-23" },
            ].map((invoice) => (
              <div
                key={invoice.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="text-gray-500"
                  >
                    <path
                      d="M13 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V9M13 2L20 9M13 2V9H20"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div>
                    <div className="font-medium">Invoice {invoice.id}</div>
                    <div className="text-sm text-muted-foreground">
                      {invoice.date}
                    </div>
                  </div>
                </div>
                <Button variant="ghost">Download</Button>
              </div>
            ))}
          </div>
        </div>

        <Separator /> */}

        {/* Team Members Section */}
        {/* <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Team Members</label>
            <p className="text-sm text-muted-foreground">
              Easily manage your team members
            </p>
          </div>
          <div className="flex-1 space-y-2">
            {[
              { id: 1, name: "Member 1", role: "Manager" },
              { id: 2, name: "Member 2", role: "Manager" },
              { id: 3, name: "Member 3", role: "Manager" },
            ].map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                      className="text-gray-500"
                    >
                      <path
                        d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <div>
                    <div className="font-medium">{member.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {member.role}
                    </div>
                  </div>
                </div>
                <Button variant="ghost">Update</Button>
              </div>
            ))}
          </div>
        </div>

        <Separator /> */}

        {/* Subscription Section */}
        <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Subscription</label>
            <p className="text-sm text-muted-foreground">
              Manage your subscription
            </p>
          </div>
          {isLoading ? (
            <div>Loading...</div>
          ) : (
            <>
              <div className="flex-1">
                <div className="flex justify-between p-4">
                  <div>
                    <div className="font-medium">
                      You are on the {subscription?.plan} plan
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-1">
                <div className="flex justify-between p-4">
                  <div>
                    {subscription?.plan === "free" ? (
                      <Link href="/pricing">
                        <Button variant="outline">
                          <BsStars />
                          Subscribe Now
                        </Button>
                      </Link>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={async () => {
                          const url = await createCustomerPortalSession(
                            accessToken,
                            activeOrg.orgId,
                          );
                          window.location.href = url;
                        }}
                      >
                        <RiUserSettingsLine />
                        Manage Subscription
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        <Separator />

        {/* Payment Method Section */}
        {/* <div className="flex flex-row">
          <div className="flex flex-col items-left w-80">
            <label className="font-semibold">Payment Method</label>
            <p className="text-sm text-muted-foreground">
              Manage your payment method
            </p>
          </div>
          <div className="flex-1">
            <div className="flex justify-between p-4">
              <div>
                <div className="font-medium">Visa ...5421</div>
                <div className="text-sm text-muted-foreground">
                  You can delete this payment method{" "}
                  <button className="text-blue-500 hover:underline">
                    here
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Separator /> */}

        {/* Danger Zone */}
        <div className="flex flex-row">
          <div>
            <Button variant="destructive" onClick={() => logoutFn(true)}>
              Sign Out
            </Button>
          </div>
        </div>

        {/* TODO: Allow deleting accounts */}
      </div>
    </div>
  );
}
