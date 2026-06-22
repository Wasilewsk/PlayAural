import AsyncStorage from "@react-native-async-storage/async-storage";
import { Alert, Linking, NativeModules, Platform } from "react-native";

import type { MobileLocalization } from "../i18n/localization";

const BATTERY_OPTIMIZATION_PROMPTED_STORAGE_KEY =
  "playaural.mobile.batteryOptimizationPrompted.v2";
const BATTERY_OPTIMIZATION_SETTINGS_ACTION =
  "android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS";

type BatteryOptimizationNativeModule = {
  isIgnoringBatteryOptimizations?: () => Promise<boolean>;
  requestIgnoreBatteryOptimizations?: () => Promise<boolean>;
};

type AndroidLinking = typeof Linking & {
  sendIntent?: (
    action: string,
    extras?: Array<{ key: string; value: boolean | number | string }>,
  ) => Promise<void>;
};

const batteryOptimizationModule =
  NativeModules.PlayAuralBatteryOptimization as BatteryOptimizationNativeModule | undefined;

async function isIgnoringBatteryOptimizations(): Promise<boolean> {
  if (Platform.OS !== "android") {
    return true;
  }
  try {
    const result = await batteryOptimizationModule?.isIgnoringBatteryOptimizations?.();
    return result ?? false;
  } catch {
    return false;
  }
}

async function requestDirectBatteryOptimizationExemption(): Promise<boolean> {
  if (Platform.OS !== "android") {
    return false;
  }
  try {
    const result = await batteryOptimizationModule?.requestIgnoreBatteryOptimizations?.();
    return result ?? false;
  } catch {
    return false;
  }
}

async function openBatteryOptimizationSettings(): Promise<void> {
  const androidLinking = Linking as AndroidLinking;
  if (typeof androidLinking.sendIntent === "function") {
    await androidLinking.sendIntent(BATTERY_OPTIMIZATION_SETTINGS_ACTION);
    return;
  }
  await Linking.openSettings();
}

export async function requestAndroidBatteryOptimizationExemptionOnce(
  localization: Pick<MobileLocalization, "t">,
  announce?: (message: string) => void,
): Promise<void> {
  if (Platform.OS !== "android") {
    return;
  }
  if (await isIgnoringBatteryOptimizations()) {
    await AsyncStorage.setItem(BATTERY_OPTIMIZATION_PROMPTED_STORAGE_KEY, "1");
    return;
  }

  const alreadyPrompted = await AsyncStorage.getItem(BATTERY_OPTIMIZATION_PROMPTED_STORAGE_KEY);
  if (alreadyPrompted) {
    return;
  }
  await AsyncStorage.setItem(BATTERY_OPTIMIZATION_PROMPTED_STORAGE_KEY, "1");

  announce?.(localization.t("battery-optimization-prompt-announcement"));

  await new Promise<void>((resolve) => {
    let resolved = false;
    const finish = () => {
      if (resolved) {
        return;
      }
      resolved = true;
      resolve();
    };

    Alert.alert(
      localization.t("battery-optimization-title"),
      localization.t("battery-optimization-message"),
      [
        {
          onPress: finish,
          style: "cancel",
          text: localization.t("battery-optimization-later"),
        },
        {
          onPress: () => {
            void requestDirectBatteryOptimizationExemption()
              .then((directPromptOpened) => {
                if (directPromptOpened) {
                  announce?.(localization.t("battery-optimization-settings-opened"));
                  return undefined;
                }
                return openBatteryOptimizationSettings().then(() => {
                  announce?.(localization.t("battery-optimization-settings-opened"));
                });
              })
              .then(() => {
                // Announcement is handled by the direct/fallback branch.
              })
              .catch(() => {
                announce?.(localization.t("battery-optimization-settings-unavailable"));
              })
              .finally(finish);
          },
          text: localization.t("battery-optimization-allow"),
        },
      ],
      {
        cancelable: true,
        onDismiss: finish,
      },
    );
  });
}
