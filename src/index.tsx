import {
  ButtonItem,
  DialogBody,
  DialogButton,
  DialogFooter,
  DialogHeader,
  ModalRoot,
  PanelSection,
  PanelSectionRow,
  showModal,
  staticClasses,
  TextField,
  ToggleField,
} from "@decky/ui";
import {
  call,
  callable,
  definePlugin,
  FileSelectionType,
  openFilePicker,
  toaster,
} from "@decky/api";
import { useState, useEffect, useCallback, useMemo } from "react";
import { FaNetworkWired } from "react-icons/fa";

interface VPNError {
  timestamp: number;
  operation: string;
  error_type: string;
  message: string;
  details: Record<string, any>;
}

interface ConfigInfo {
  name: string;
  interface: string;
  active: boolean;
  managed_by: string;
}

interface VPNOpResult {
  success: boolean;
  error: string | null;
  interface: string;
}

const listConfigsWithStatus = callable<[], ConfigInfo[]>(
  "list_configs_with_status",
);
const vpnStartConfig = callable<[{ config_name: string }], VPNOpResult>(
  "vpn_start_config",
);
const vpnStopConfig = callable<[{ config_name: string }], VPNOpResult>(
  "vpn_stop_config",
);
const getErrors = callable<[], VPNError[]>("get_errors");
const clearErrors = callable<[], boolean>("clear_errors");

interface DeleteConfigResult {
  success: boolean;
  config_name: string | null;
  error?: string | null;
}
const deleteVpnConfig = callable<[{ name: string }] | [string], DeleteConfigResult>(
  "delete_vpn_config"
);

interface SymlinkRepairItem {
  name: string;
  interface: string;
  ok: boolean;
  action: "none" | "created" | "replaced" | "error";
  error: string | null;
}
interface SymlinkRepairResult {
  total: number;
  repaired: number;
  results: SymlinkRepairItem[];
}
const repairSymlinks = callable<[], SymlinkRepairResult>("repair_symlinks");

interface DiagnosticsProbe {
  name: string;
  kind: "ping" | "http";
  target: string;
  ok: boolean;
  detail: string;
  latency_ms: number | null;
}
const diagnoseConnectivity = callable<[], DiagnosticsProbe[]>("diagnose_connectivity");
const generateWarpConfig = callable<[], { success: boolean; error?: string }>("generate_warp_config");
const getSteamLanguage = callable<[], string>("get_steam_language");
const getDownloadsDir = callable<[], string>("get_downloads_dir");

type TranslationKeys =
  | "vpnConfigs"
  | "noConfigs"
  | "importConfig"
  | "diagnostics"
  | "checkConn"
  | "checking"
  | "restoreSymlinks"
  | "restoring"
  | "errors"
  | "hideErrors"
  | "viewErrors"
  | "clearErrors"
  | "noErrors"
  | "deleteConfig"
  | "deleteConfirm"
  | "delete"
  | "deleting"
  | "cancel"
  | "warpGenerator"
  | "generatingWarp"
  | "updateWarp"
  | "configName"
  | "configNameDesc"
  | "selectConfFile"
  | "selectOtherFile"
  | "success"
  | "error"
  | "vpnEnabled"
  | "vpnDisabled"
  | "available"
  | "restoredXofY"
  | "details"
  | "type"
  | "message"
  | "importing"
  | "configSaved"
  | "configImported"
  | "importError"
  | "deleteError"
  | "configDeleted"
  | "configNameErrorEmpty"
  | "configNameErrorLength"
  | "configNameErrorRegex";

const translations: Record<string, Record<TranslationKeys, string>> = {
  english: {
    vpnConfigs: "VPN Configs",
    noConfigs: "No imported configs",
    importConfig: "Import config",
    diagnostics: "Diagnostics",
    checkConn: "Check connection",
    checking: "Checking...",
    restoreSymlinks: "Restore symlinks",
    restoring: "Restoring...",
    errors: "Errors",
    hideErrors: "Hide errors",
    viewErrors: "View errors",
    clearErrors: "Clear error history",
    noErrors: "No errors detected",
    deleteConfig: "Delete config",
    deleteConfirm: 'Delete config "{name}"? Interface will be stopped.',
    delete: "Delete",
    deleting: "Deleting...",
    cancel: "Cancel",
    warpGenerator: "WARP GENERATOR",
    generatingWarp: "Generating WARP...",
    updateWarp: "Update",
    configName: "Config name",
    configNameDesc: "up to 12 chars: a-z, 0-9, _ = + . -",
    selectConfFile: "Select .conf file",
    selectOtherFile: "Select another file",
    success: "Success",
    error: "Error",
    vpnEnabled: "VPN Enabled",
    vpnDisabled: "VPN Disabled",
    available: "available",
    restoredXofY: "Restored {restored} of {total}",
    details: "Details",
    type: "Type",
    message: "Message",
    importing: "Importing...",
    configSaved: "Config saved",
    configImported: "Config imported",
    importError: "Import failed",
    deleteError: "Delete failed",
    configDeleted: "Config deleted",
    configNameErrorEmpty: "Enter config name",
    configNameErrorLength: "Max {max} characters",
    configNameErrorRegex: "Only letters, numbers, and symbols _ = + . -",
  },
  russian: {
    vpnConfigs: "VPN Конфиги",
    noConfigs: "Нет импортированных конфигов",
    importConfig: "Импортировать конфиг",
    diagnostics: "Диагностика",
    checkConn: "Проверить связь",
    checking: "Проверка…",
    restoreSymlinks: "Восстановить симлинки",
    restoring: "Восстановление…",
    errors: "Ошибки",
    hideErrors: "Скрыть ошибки",
    viewErrors: "Просмотр ошибок",
    clearErrors: "Очистить историю ошибок",
    noErrors: "Ошибок не обнаружено",
    deleteConfig: "Удалить конфиг",
    deleteConfirm: "Удалить конфиг «{name}»? Интерфейс будет остановлен.",
    delete: "Удалить",
    deleting: "Удаление…",
    cancel: "Отмена",
    warpGenerator: "WARP GENERATOR",
    generatingWarp: "Генерация WARP...",
    updateWarp: "Обновить",
    configName: "Имя конфига",
    configNameDesc: "до 12 символов: a-z, 0-9, _ = + . -",
    selectConfFile: "Выбрать файл .conf",
    selectOtherFile: "Выбрать другой файл",
    success: "Успех",
    error: "Ошибка",
    vpnEnabled: "VPN включён",
    vpnDisabled: "VPN выключен",
    available: "доступно",
    restoredXofY: "Восстановлено {restored} из {total}",
    details: "Детали",
    type: "Тип",
    message: "Сообщение",
    importing: "Импорт...",
    configSaved: "Конфиг сохранён",
    configImported: "Конфиг импортирован",
    importError: "Ошибка импорта",
    deleteError: "Ошибка удаления",
    configDeleted: "Конфиг удалён",
    configNameErrorEmpty: "Введите имя конфига",
    configNameErrorLength: "Макс. {max} символов (как в имени интерфейса)",
    configNameErrorRegex: "Только буквы, цифры и символы _ = + . -",
  },
  schinese: {
    vpnConfigs: "VPN 配置",
    noConfigs: "无导入的配置",
    importConfig: "导入配置",
    diagnostics: "诊断",
    checkConn: "测试连接",
    checking: "正在诊断...",
    restoreSymlinks: "修复软链接",
    restoring: "正在修复...",
    errors: "错误",
    hideErrors: "隐藏错误",
    viewErrors: "查看错误",
    clearErrors: "清除错误历史",
    noErrors: "未检测到错误",
    deleteConfig: "删除配置",
    deleteConfirm: '确定删除配置 "{name}" 吗？接口将被停止。',
    delete: "删除",
    deleting: "正在删除...",
    cancel: "取消",
    warpGenerator: "WARP 生成器",
    generatingWarp: "正在生成 WARP...",
    updateWarp: "更新",
    configName: "配置名称",
    configNameDesc: "最多 12 个字符：a-z, 0-9, _ = + . -",
    selectConfFile: "选择 .conf 文件",
    selectOtherFile: "选择其他文件",
    success: "成功",
    error: "错误",
    vpnEnabled: "VPN 已启用",
    vpnDisabled: "VPN 已禁用",
    available: "可用",
    restoredXofY: "已修复 {restored} / {total}",
    details: "详情",
    type: "类型",
    message: "消息",
    importing: "正在导入...",
    configSaved: "配置已保存",
    configImported: "配置已导入",
    importError: "导入失败",
    deleteError: "删除失败",
    configDeleted: "配置已删除",
    configNameErrorEmpty: "请输入配置名称",
    configNameErrorLength: "最多 {max} 个字符",
    configNameErrorRegex: "仅限字母、数字以及 _ = + . -",
  },
  tchinese: {
    vpnConfigs: "VPN 配置",
    noConfigs: "無匯入的配置",
    importConfig: "匯入配置",
    diagnostics: "診斷",
    checkConn: "測試連線",
    checking: "正在診斷...",
    restoreSymlinks: "修復軟連結",
    restoring: "正在修復...",
    errors: "錯誤",
    hideErrors: "隱藏錯誤",
    viewErrors: "查看錯誤",
    clearErrors: "清除錯誤歷史",
    noErrors: "未檢測到錯誤",
    deleteConfig: "刪除配置",
    deleteConfirm: '確定刪除配置 "{name}" 嗎？介面將被停止。',
    delete: "刪除",
    deleting: "正在刪除...",
    cancel: "取消",
    warpGenerator: "WARP 生成器",
    generatingWarp: "正在生成 WARP...",
    updateWarp: "更新",
    configName: "配置名稱",
    configNameDesc: "最多 12 個字元：a-z, 0-9, _ = + . -",
    selectConfFile: "選擇 .conf 檔案",
    selectOtherFile: "選擇其他檔案",
    success: "成功",
    error: "錯誤",
    vpnEnabled: "VPN 已啟用",
    vpnDisabled: "VPN 已禁用",
    available: "可用",
    restoredXofY: "已修復 {restored} / {total}",
    details: "詳情",
    type: "類型",
    message: "訊息",
    importing: "正在匯入...",
    configSaved: "配置已儲存",
    configImported: "配置已匯入",
    importError: "匯入失敗",
    deleteError: "刪除失敗",
    configDeleted: "配置已刪除",
    configNameErrorEmpty: "請輸入配置名稱",
    configNameErrorLength: "最多 {max} 個字元",
    configNameErrorRegex: "僅限字母、數字以及 _ = + . -",
  },
  arabic: {
    vpnConfigs: "إعدادات الـ VPN",
    noConfigs: "لا توجد ملفات تهيئة مستوردة",
    importConfig: "استيراد ملف تهيئة",
    diagnostics: "التشخيص",
    checkConn: "التحقق من الاتصال",
    checking: "جاري التحقق...",
    restoreSymlinks: "استعادة الروابط الرمزية",
    restoring: "جاري الاستعادة...",
    errors: "الأخطاء",
    hideErrors: "إخفاء الأخطاء",
    viewErrors: "عرض الأخطاء",
    clearErrors: "مسح سجل الأخطاء",
    noErrors: "لم يتم العثور على أخطاء",
    deleteConfig: "حذف ملف التهيئة",
    deleteConfirm: 'حذف ملف التهيئة "{name}"؟ سيتم إيقاف الواجهة.',
    delete: "حذف",
    deleting: "جاري الحذف...",
    cancel: "إلغاء",
    warpGenerator: "مولد WARP",
    generatingWarp: "جاري توليد WARP...",
    updateWarp: "تحديث",
    configName: "اسم ملف التهيئة",
    configNameDesc: "حتى 12 حرفًا: a-z, 0-9, _ = + . -",
    selectConfFile: "اختر ملف .conf",
    selectOtherFile: "اختر ملفًا آخر",
    success: "نجاح",
    error: "خطأ",
    vpnEnabled: "تم تفعيل الـ VPN",
    vpnDisabled: "تم إيقاف الـ VPN",
    available: "متاح",
    restoredXofY: "تم استعادة {restored} من {total}",
    details: "التفاصيل",
    type: "النوع",
    message: "الرسالة",
    importing: "جاري الاستيراد...",
    configSaved: "تم حفظ ملف التهيئة",
    configImported: "تم استيراد ملف التهيئة",
    importError: "فشل الاستيراد",
    deleteError: "فشل الحذف",
    configDeleted: "تم حذف ملف التهيئة",
    configNameErrorEmpty: "أدخل اسم ملف التهيئة",
    configNameErrorLength: "الحد الأقصى {max} حرفًا",
    configNameErrorRegex: "الأحرف والأرقام والرموز فقط _ = + . -",
  },
  persian: {
    vpnConfigs: "پیکربندی‌های VPN",
    noConfigs: "هیچ پیکربندی وارد نشده است",
    importConfig: "وارد کردن پیکربندی",
    diagnostics: "عیب‌یابی",
    checkConn: "بررسی اتصال",
    checking: "در حال بررسی...",
    restoreSymlinks: "بازیابی پیوندهای نمادین",
    restoring: "در حال بازیابی...",
    errors: "خطاها",
    hideErrors: "پنهان کردن خطاها",
    viewErrors: "مشاهده خطاها",
    clearErrors: "پاک کردن تاریخچه خطاها",
    noErrors: "هیچ خطایی شناسایی نشد",
    deleteConfig: "حذف پیکربندی",
    deleteConfirm: 'پیکربندی "{name}" حذف شود؟ رابط کاربری متوقف خواهد شد.',
    delete: "حذف",
    deleting: "در حال حذف...",
    cancel: "لغو",
    warpGenerator: "سازنده WARP",
    generatingWarp: "در حال ساخت WARP...",
    updateWarp: "به‌روزرسانی",
    configName: "نام پیکربندی",
    configNameDesc: "تا ۱۲ نویسه: a-z, 0-9, _ = + . -",
    selectConfFile: "انتخاب فایل .conf",
    selectOtherFile: "انتخاب فایلی دیگر",
    success: "موفقیت",
    error: "خطا",
    vpnEnabled: "VPN فعال شد",
    vpnDisabled: "VPN غیرفعال شد",
    available: "در دسترس",
    restoredXofY: "بازیابی {restored} از {total}",
    details: "جزئیات",
    type: "نوع",
    message: "پیام",
    importing: "در حال وارد کردن...",
    configSaved: "پیکربندی ذخیره شد",
    configImported: "پیکربندی وارد شد",
    importError: "وارد کردن ناموفق بود",
    deleteError: "حذف ناموفق بود",
    configDeleted: "پیکربندی حذف شد",
    configNameErrorEmpty: "نام پیکربندی را وارد کنید",
    configNameErrorLength: "حداکثر {max} نویسه",
    configNameErrorRegex: "فقط حروف، اعداد و نمادهای _ = + . -",
  },
  turkish: {
    vpnConfigs: "VPN Yapılandırmaları",
    noConfigs: "İçe aktarılmış yapılandırma yok",
    importConfig: "Yapılandırmayı içe aktar",
    diagnostics: "Tanılama",
    checkConn: "Bağlantıyı kontrol et",
    checking: "Kontrol ediliyor...",
    restoreSymlinks: "Sembolik bağlantıları geri yükle",
    restoring: "Geri yükleniyor...",
    errors: "Hatalar",
    hideErrors: "Hataları gizle",
    viewErrors: "Hataları göster",
    clearErrors: "Hata geçmişini temizle",
    noErrors: "Hata tespit edilmedi",
    deleteConfig: "Yapılandırmayı sil",
    deleteConfirm: '"{name}" yapılandırması silinsin mi? Arayüz durdurulacak.',
    delete: "Sil",
    deleting: "Siliniyor...",
    cancel: "İptal",
    warpGenerator: "WARP ÜRETİCİ",
    generatingWarp: "WARP üretiliyor...",
    updateWarp: "Güncelle",
    configName: "Yapılandırma adı",
    configNameDesc: "12 karaktere kadar: a-z, 0-9, _ = + . -",
    selectConfFile: ".conf dosyası seç",
    selectOtherFile: "Başka bir dosya seç",
    success: "Başarılı",
    error: "Hata",
    vpnEnabled: "VPN Etkinleştirildi",
    vpnDisabled: "VPN Devre Dışı",
    available: "aktif",
    restoredXofY: "{total} sembolik bağlantıdan {restored} tanesi geri yüklendi",
    details: "Detaylar",
    type: "Tip",
    message: "Mesaj",
    importing: "İçe aktarılıyor...",
    configSaved: "Yapılandırma kaydedildi",
    configImported: "Yapılandırma içe aktarıldı",
    importError: "İçe aktarma başarısız",
    deleteError: "Silme başarısız",
    configDeleted: "Yapılandırma silindi",
    configNameErrorEmpty: "Yapılandırma adını girin",
    configNameErrorLength: "En fazla {max} karakter",
    configNameErrorRegex: "Sadece harf, rakam ve _ = + . - karakterleri",
  }
};

// Aliases for Persian/Farsi
translations.farsi = translations.persian;

type TFunc = (key: TranslationKeys, params?: Record<string, string>) => string;

// Валидация имени конфига: как в awg-quick и config_manager (интерфейс = vd-<name>, макс. 15 символов)
const CONFIG_NAME_MAX_LEN = 12; // 3 (префикс "vd-") + 12 = 15
const CONFIG_NAME_REGEX = /^[a-zA-Z0-9_=+.-]+$/;

function formatTimestamp(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString();
}

function validateConfigName(name: string, t: TFunc): { valid: boolean; error?: string } {
  const trimmed = name.trim();
  if (!trimmed) {
    return { valid: false, error: t("configNameErrorEmpty") };
  }
  if (trimmed.length > CONFIG_NAME_MAX_LEN) {
    return {
      valid: false,
      error: t("configNameErrorLength", { max: String(CONFIG_NAME_MAX_LEN) }),
    };
  }
  if (!CONFIG_NAME_REGEX.test(trimmed)) {
    return {
      valid: false,
      error: t("configNameErrorRegex"),
    };
  }
  return { valid: true };
}

function ImportConfigModal({
  closeModal,
  onSuccess,
  t,
}: {
  closeModal?: () => void;
  onSuccess: () => void;
  t: TFunc;
}) {
  const [name, setName] = useState("");
  const [filePath, setFilePath] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [downloadsDir, setDownloadsDir] = useState("/home/deck/Downloads");

  useEffect(() => {
    getDownloadsDir()
      .then((dir) => {
        if (dir) {
          setDownloadsDir(dir);
        }
      })
      .catch(console.error);
  }, []);

  const handlePickFile = async () => {
    try {
      const res = await openFilePicker(
        FileSelectionType.FILE,
        downloadsDir,
        true,
        true,
        undefined,
        ["conf"],
      );
      const filename =
        res.realpath
          .split("/")
          .pop()
          ?.replace(/\.conf$/, "") ?? "";
      setFilePath(res.realpath);
      setName(filename);
      setStatus(res.realpath.split("/").pop() ?? "");
    } catch (e) {
      console.error(e);
    }
  };

  const handleImport = async () => {
    try {
      const validation = validateConfigName(name, t);
      if (!validation.valid) {
        toaster.toast({ title: t("error"), body: validation.error ?? "" });
        return;
      }
      const trimmedName = name.trim();

      setLoading(true);
      setStatus(t("importing"));

      const result = await call<
        [string, string],
        { success: boolean; error: string }
      >("import_vpn_config", trimmedName, filePath);
      if (result.success) {
        setStatus(t("configSaved"));
        toaster.toast({ title: t("configImported"), body: trimmedName });
        onSuccess();
        closeModal?.();
      } else {
        setStatus("");
        toaster.toast({
          title: t("importError"),
          body: result.error ?? "",
        });
      }
    } catch (e) {
      setStatus("");
      toaster.toast({ title: t("error"), body: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalRoot onCancel={closeModal} closeModal={closeModal}>
      <DialogHeader>{t("importConfig")}</DialogHeader>
      <DialogBody>
        <DialogButton onClick={handlePickFile} disabled={loading}>
          {filePath ? t("selectOtherFile") : t("selectConfFile")}
        </DialogButton>
        {filePath && (
          <div style={{ marginTop: "12px" }}>
            <TextField
              label={t("configName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              description={t("configNameDesc")}
            />
          </div>
        )}
        {status && (
          <div style={{ marginTop: "8px", fontSize: "12px", color: "#8b929a" }}>
            {status}
          </div>
        )}
      </DialogBody>
      <DialogFooter>
        <DialogButton
          onClick={handleImport}
          disabled={loading}
        >
          {loading ? t("importing") : t("importConfig")}
        </DialogButton>
        <DialogButton onClick={closeModal}>{t("cancel")}</DialogButton>
      </DialogFooter>
    </ModalRoot>
  );
}

function DeleteConfigModal({
  configName,
  closeModal,
  onSuccess,
  t,
}: {
  configName: string;
  closeModal?: () => void;
  onSuccess: () => void;
  t: TFunc;
}) {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    try {
      setLoading(true);
      const result = await deleteVpnConfig({ name: configName });
      if (result.success) {
        toaster.toast({ title: t("configDeleted"), body: configName });
        onSuccess();
        closeModal?.();
      } else {
        toaster.toast({
          title: t("deleteError"),
          body: result.error ?? "",
        });
      }
    } catch (e) {
      toaster.toast({ title: t("error"), body: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalRoot onCancel={closeModal} closeModal={closeModal}>
      <DialogHeader>{t("deleteConfig")}</DialogHeader>
      <DialogBody>
        <div style={{ fontSize: "14px" }}>
          {t("deleteConfirm", { name: configName })}
        </div>
      </DialogBody>
      <DialogFooter>
        <DialogButton onClick={handleDelete} disabled={loading}>
          {loading ? t("deleting") : t("delete")}
        </DialogButton>
        <DialogButton onClick={closeModal}>{t("cancel")}</DialogButton>
      </DialogFooter>
    </ModalRoot>
  );
}

function Content() {
  const [lang, setLang] = useState<string>("english");
  const [configs, setConfigs] = useState<ConfigInfo[]>([]);
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<VPNError[]>([]);
  const [showErrors, setShowErrors] = useState<boolean>(false);
  const [probes, setProbes] = useState<DiagnosticsProbe[] | null>(null);
  const [probesLoading, setProbesLoading] = useState<boolean>(false);
  const [repairLoading, setRepairLoading] = useState<boolean>(false);
  const [warpGenerating, setWarpGenerating] = useState<boolean>(false);

  const t = useMemo<TFunc>(() => {
    return (key: TranslationKeys, params?: Record<string, string>) => {
      const dict = translations[lang] || translations.english;
      let val = dict[key] || translations.english[key] || String(key);
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          val = val.replace(`{${k}}`, v);
        });
      }
      return val;
    };
  }, [lang]);

  const refreshConfigs = useCallback(async () => {
    try {
      const result = await listConfigsWithStatus();
      setConfigs(result);
    } catch (error) {
      console.error("Failed to refresh configs:", error);
    }
  }, []);

  const loadErrors = useCallback(async () => {
    try {
      const errorList = await getErrors();
      setErrors(errorList);
    } catch (error) {
      console.error("Failed to load errors:", error);
    }
  }, []);

  const handleToggle = useCallback(
    async (configName: string, enabled: boolean) => {
      setLoadingMap((prev) => ({ ...prev, [configName]: true }));
      try {
        const result = enabled
          ? await vpnStartConfig({ config_name: configName })
          : await vpnStopConfig({ config_name: configName });

        if (!result.success) {
          toaster.toast({
            title: t("error"),
            body: result.error ?? "",
          });
          await loadErrors();
        } else {
          toaster.toast({
            title: enabled ? t("vpnEnabled") : t("vpnDisabled"),
            body: configName,
          });
        }
      } catch (error) {
        toaster.toast({
          title: t("error"),
          body: String(error),
        });
        await loadErrors();
      } finally {
        setLoadingMap((prev) => ({ ...prev, [configName]: false }));
        await refreshConfigs();
      }
    },
    [refreshConfigs, loadErrors, t],
  );

  const handleDiagnose = useCallback(async () => {
    setProbesLoading(true);
    try {
      const res = await diagnoseConnectivity();
      setProbes(res);
      const ok = res.filter((p) => p.ok).length;
      toaster.toast({
        title: t("checkConn"),
        body: `${ok}/${res.length} ${t("available")}`,
      });
    } catch (e) {
      toaster.toast({ title: t("error"), body: String(e) });
    } finally {
      setProbesLoading(false);
    }
  }, [t]);

  const handleRepairSymlinks = useCallback(async () => {
    setRepairLoading(true);
    try {
      const res = await repairSymlinks();
      toaster.toast({
        title: t("restoreSymlinks"),
        body: t("restoredXofY", { restored: String(res.repaired), total: String(res.total) }),
      });
      await refreshConfigs();
    } catch (e) {
      toaster.toast({ title: t("error"), body: String(e) });
    } finally {
      setRepairLoading(false);
    }
  }, [refreshConfigs, t]);

  const handleClearErrors = useCallback(async () => {
    try {
      await clearErrors();
      setErrors([]);
      toaster.toast({ title: t("clearErrors"), body: "" });
    } catch (error) {
      toaster.toast({ title: t("error"), body: String(error) });
    }
  }, [t]);

  const handleGenerateWarp = useCallback(async () => {
    setWarpGenerating(true);
    try {
      const result = await generateWarpConfig();
      if (result.success) {
        toaster.toast({
          title: t("success"),
          body: t("vpnEnabled") + ": warp-deck",
        });
      } else {
        toaster.toast({
          title: t("error"),
          body: result.error || "Unknown error",
        });
      }
    } catch (e) {
      toaster.toast({
        title: t("error"),
        body: String(e),
      });
    } finally {
      setWarpGenerating(false);
      await refreshConfigs();
    }
  }, [refreshConfigs, t]);

  useEffect(() => {
    // Получение языка Steam
    getSteamLanguage().then((detectedLang) => {
      if (translations[detectedLang]) {
        setLang(detectedLang);
      }
    }).catch(console.error);

    refreshConfigs();
    loadErrors();

    const configsInterval = setInterval(refreshConfigs, 3000);
    const errorsInterval = setInterval(loadErrors, 10000);

    return () => {
      clearInterval(configsInterval);
      clearInterval(errorsInterval);
    };
  }, [refreshConfigs, loadErrors]);

  const hasWarp = useMemo(() => {
    return configs.some(c => c.name === "warp-deck");
  }, [configs]);

  return (
    <>
      <PanelSection title={t("vpnConfigs")}>
        {configs.length === 0 && !hasWarp && (
          <PanelSectionRow>
            <div style={{ color: "#888", fontSize: "14px" }}>
              {t("noConfigs")}
            </div>
          </PanelSectionRow>
        )}
        
        {/* Кнопка генератора WARP, если конфига нет */}
        {!hasWarp && (
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              disabled={warpGenerating}
              onClick={handleGenerateWarp}
            >
              {warpGenerating ? t("generatingWarp") : t("warpGenerator")}
            </ButtonItem>
          </PanelSectionRow>
        )}

        {configs.map((cfg) => (
          <PanelSectionRow key={cfg.interface}>
            <ToggleField
              label={cfg.name}
              description={cfg.interface}
              checked={cfg.active}
              disabled={!!loadingMap[cfg.name]}
              onChange={(val) => handleToggle(cfg.name, val)}
            />
            <div style={{ marginTop: "4px", display: "flex", flexDirection: "column", gap: "4px" }}>
              <ButtonItem
                layout="below"
                onClick={() =>
                  showModal(
                    <DeleteConfigModal
                      configName={cfg.name}
                      onSuccess={refreshConfigs}
                      t={t}
                    />
                  )
                }
              >
                {t("deleteConfig")}
              </ButtonItem>
              
              {/* Кнопка обновления конфига WARP, если это warp-deck */}
              {cfg.name === "warp-deck" && (
                <ButtonItem
                  layout="below"
                  disabled={warpGenerating || !!loadingMap[cfg.name]}
                  onClick={handleGenerateWarp}
                >
                  {warpGenerating ? t("generatingWarp") : t("updateWarp")}
                </ButtonItem>
              )}
            </div>
          </PanelSectionRow>
        ))}
        
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={() =>
              showModal(<ImportConfigModal onSuccess={refreshConfigs} t={t} />)
            }
          >
            {t("importConfig")}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title={t("diagnostics")}>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={probesLoading}
            onClick={handleDiagnose}
          >
            {probesLoading ? t("checking") : t("checkConn")}
          </ButtonItem>
        </PanelSectionRow>
        {probes && probes.map((p, i) => (
          <PanelSectionRow key={`${p.name}-${i}`}>
            <div
              style={{
                padding: "8px",
                fontSize: "12px",
                borderLeft: `3px solid ${p.ok ? "#4ade80" : "#f87171"}`,
                paddingLeft: "10px",
                marginBottom: "4px",
              }}
            >
              <div style={{ fontWeight: "bold" }}>
                {p.ok ? "✓" : "✗"} {p.name}
              </div>
              <div style={{ color: "#8b929a" }}>{p.detail}</div>
            </div>
          </PanelSectionRow>
        ))}
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={repairLoading}
            onClick={handleRepairSymlinks}
          >
            {repairLoading ? t("restoring") : t("restoreSymlinks")}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title={t("errors")}>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={() => {
              setShowErrors(!showErrors);
              if (!showErrors) loadErrors();
            }}
          >
            {showErrors
              ? t("hideErrors")
              : `${t("viewErrors")}${errors.length > 0 ? ` (${errors.length})` : ""}`}
          </ButtonItem>
        </PanelSectionRow>

        {showErrors && (
          <>
            {errors.length > 0 && (
              <PanelSectionRow>
                <ButtonItem layout="below" onClick={handleClearErrors}>
                  {t("clearErrors")}
                </ButtonItem>
              </PanelSectionRow>
            )}

            {errors.length === 0 ? (
              <PanelSectionRow>
                <div
                  style={{
                    padding: "10px",
                    textAlign: "center",
                    color: "#888",
                    fontSize: "14px",
                  }}
                >
                  {t("noErrors")}
                </div>
              </PanelSectionRow>
            ) : (
              errors
                .slice()
                .reverse()
                .map((error) => (
                  <PanelSectionRow key={`${error.timestamp}-${error.operation}`}>
                    <div
                      style={{
                        padding: "12px",
                        backgroundColor: "rgba(255, 0, 0, 0.1)",
                        borderRadius: "4px",
                        marginBottom: "8px",
                        fontSize: "12px",
                      }}
                    >
                      <div style={{ marginBottom: "4px", fontWeight: "bold" }}>
                        {formatTimestamp(error.timestamp)} - {error.operation}
                      </div>
                      <div style={{ marginBottom: "4px", color: "#FF6B6B" }}>
                        <strong>{t("type")}:</strong> {error.error_type}
                      </div>
                      <div style={{ marginBottom: "4px" }}>
                        <strong>{t("message")}:</strong> {error.message}
                      </div>
                      {Object.keys(error.details).length > 0 && (
                        <details style={{ marginTop: "8px" }}>
                          <summary style={{ cursor: "pointer", color: "#888" }}>
                            {t("details")}
                          </summary>
                          <pre
                            style={{
                              marginTop: "4px",
                              padding: "8px",
                              backgroundColor: "rgba(0, 0, 0, 0.3)",
                              borderRadius: "4px",
                              fontSize: "11px",
                              overflow: "auto",
                            }}
                          >
                            {JSON.stringify(error.details, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </PanelSectionRow>
                ))
            )}
          </>
        )}
      </PanelSection>
    </>
  );
}

export default definePlugin(() => {
  console.log("WARP Deck plugin initializing");

  return {
    name: "WARP Deck",
    titleView: <div className={staticClasses.Title}>WARP Deck</div>,
    content: <Content />,
    icon: <FaNetworkWired />,
    onDismount() {
      console.log("WARP Deck plugin unloading");
    },
  };
});
