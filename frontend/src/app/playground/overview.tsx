import { BetaAlert } from "@/components/playground/beta-alert";
import * as motion from "motion/react-client";
import Image from "next/image";

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-12"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl p-6 flex flex-col leading-relaxed text-center max-w-xl">
        <div className="flex flex-col gap-4 mb-24">
          <BetaAlert />
        </div>
        <p className="flex flex-row justify-center gap-4 items-center mb-36">
          <Image
            src="/aci-dev-full-logo.svg"
            alt="ACI.dev Logo"
            width={241}
            height={48}
            className="w-auto h-6"
          />
        </p>
        <h1 className="text-2xl font-bold mb-2 sm:mb-4 text-transparent bg-clip-text bg-gradient-to-r from-gray-900 to-gray-700 dark:from-gray-100 dark:to-gray-300">
          Hi, <span className="text-primary/80">Agent Builder</span>
        </h1>
        <h2 className="text-xl sm:text-xl md:text-xl font-medium mb-4 sm:mb-8 text-transparent bg-clip-text bg-gradient-to-r from-gray-800 to-gray-600 dark:from-gray-200 dark:to-gray-400">
          How can I help you today?
        </h2>
      </div>
    </motion.div>
  );
};
