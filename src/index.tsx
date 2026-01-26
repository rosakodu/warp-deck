import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  staticClasses,
  ToggleField,
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api"
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { FaNetworkWired, FaExclamationTriangle, FaCheckCircle, FaTimesCircle } from "react-icons/fa";

// Типы для ошибок
interface VPNError {
  timestamp: number;
  operation: string;
  error_type: string;
  message: string;
  details: Record<string, any>;
}

interface VPNStatusResponse {
  status: string;
  error: VPNError | null;
}

interface VPNOperationResponse {
  success: boolean;
  error: VPNError | null;
}

// Callable функции для вызова Python методов
const vpnStart = callable<[], VPNOperationResponse>("vpn_start");
const vpnStop = callable<[], VPNOperationResponse>("vpn_stop");
const vpnStatus = callable<[], VPNStatusResponse>("vpn_status");
const getErrors = callable<[], VPNError[]>("get_errors");
const clearErrors = callable<[], boolean>("clear_errors");

function Content() {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>("unknown");
  const [errors, setErrors] = useState<VPNError[]>([]);
  const [showErrors, setShowErrors] = useState<boolean>(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const toggleDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const lastStatusCheckRef = useRef<number>(0);
  const statusRef = useRef<string>("unknown");

  // Функция для форматирования времени
  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  // Функция для получения статуса VPN с debounce
  const checkStatus = useCallback(async (showToast: boolean = false, force: boolean = false) => {
    const now = Date.now();
    // Throttle: не проверяем чаще чем раз в секунду (если не force)
    if (!force && now - lastStatusCheckRef.current < 1000) {
      return;
    }
    lastStatusCheckRef.current = now;

    try {
      const response = await vpnStatus();
      const newStatus = response.status;
      setStatus(newStatus);
      statusRef.current = newStatus; // Обновляем ref
      setIsActive(newStatus === "active");

      if (response.error && showToast) {
        // Не показываем toast для ошибок при polling
        console.error("Status check error:", response.error);
      }
    } catch (error) {
      console.error("Failed to check VPN status:", error);
      if (showToast) {
        toaster.toast({
          title: "Ошибка проверки статуса",
          body: String(error)
        });
      }
    }
  }, []);

  // Функция для загрузки ошибок
  const loadErrors = async () => {
    try {
      const errorList = await getErrors();
      setErrors(errorList);
    } catch (error) {
      console.error("Failed to load errors:", error);
    }
  };

  // Функция для переключения VPN с debounce
  const handleToggle = useCallback(async (enabled: boolean) => {
    if (isLoading) return;
    
    // Сохраняем текущее состояние перед операцией
    const previousState = isActive;
    
    // Debounce: очищаем предыдущий таймер если есть
    if (toggleDebounceRef.current) {
      clearTimeout(toggleDebounceRef.current);
    }
    
    // Устанавливаем новый таймер для debounce (300ms)
    toggleDebounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        let response: VPNOperationResponse;
        
        if (enabled) {
          response = await vpnStart();
        } else {
          response = await vpnStop();
        }

        if (response.success) {
          setIsActive(enabled);
          toaster.toast({
            title: enabled ? "VPN включен" : "VPN выключен",
            body: `Статус успешно изменен`
          });
          // Обновляем статус после операции (force для немедленного обновления)
          await checkStatus(false, true);
          // Загружаем ошибки на случай если были
          await loadErrors();
        } else {
          // При ошибке НЕ меняем состояние тумблера - оставляем как было
          // Тумблер автоматически вернется в исходное состояние через polling
          if (response.error) {
            toaster.toast({
              title: "Ошибка",
              body: response.error.message
            });
            await loadErrors();
          }
          // Обновляем статус чтобы синхронизировать UI
          await checkStatus(false, true);
        }
      } catch (error) {
        // При ошибке НЕ меняем состояние тумблера
        toaster.toast({
          title: "Ошибка",
          body: String(error)
        });
        await loadErrors();
        // Обновляем статус чтобы синхронизировать UI
        await checkStatus(false, true);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, [isLoading, checkStatus, isActive]);

  // Функция для очистки ошибок
  const handleClearErrors = async () => {
    try {
      await clearErrors();
      setErrors([]);
      toaster.toast({
        title: "История ошибок очищена",
        body: ""
      });
    } catch (error) {
      toaster.toast({
        title: "Ошибка очистки",
        body: String(error)
      });
    }
  };

  // Polling статуса
  useEffect(() => {
    // Первоначальная проверка статуса
    checkStatus(false, true);
    loadErrors();

    // Простой интервал polling каждые 3 секунды
    pollingIntervalRef.current = setInterval(() => {
      checkStatus(false);
    }, 3000);

    // Очистка при размонтировании
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      if (toggleDebounceRef.current) {
        clearTimeout(toggleDebounceRef.current);
      }
    };
  }, [checkStatus]);

  // Мемоизация иконки статуса
  const statusIcon = useMemo(() => {
    if (status === "active") {
      return <FaCheckCircle style={{ color: "#1DB954", marginRight: "8px" }} />;
    } else if (status === "inactive") {
      return <FaTimesCircle style={{ color: "#888", marginRight: "8px" }} />;
    } else {
      return <FaExclamationTriangle style={{ color: "#FFA500", marginRight: "8px" }} />;
    }
  }, [status]);

  // Мемоизация текста статуса
  const statusText = useMemo(() => {
    if (status === "active") return "Активен";
    if (status === "inactive") return "Неактивен";
    return "Неизвестно";
  }, [status]);

  return (
    <>
      <PanelSection title="Управление VPN">
        <PanelSectionRow>
          <ToggleField
            label="AmneziaWG VPN"
            description={isLoading ? "Выполняется операция..." : statusText}
            checked={isActive}
            disabled={isLoading}
            onChange={handleToggle}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <div style={{
            display: "flex",
            alignItems: "center",
            padding: "10px",
            backgroundColor: "rgba(255, 255, 255, 0.05)",
            borderRadius: "4px"
          }}>
            {statusIcon}
            <span style={{ fontSize: "14px" }}>
              Статус: <strong>{statusText}</strong>
            </span>
          </div>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Ошибки">
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            onClick={() => {
              setShowErrors(!showErrors);
              if (!showErrors) {
                loadErrors();
              }
            }}
          >
            {showErrors ? "Скрыть ошибки" : `Просмотр ошибок${errors.length > 0 ? ` (${errors.length})` : ""}`}
          </ButtonItem>
        </PanelSectionRow>

        {showErrors && (
          <>
            {errors.length > 0 && (
              <PanelSectionRow>
                <ButtonItem
                  layout="below"
                  onClick={handleClearErrors}
                >
                  Очистить историю ошибок
                </ButtonItem>
              </PanelSectionRow>
            )}

            {errors.length === 0 ? (
              <PanelSectionRow>
                <div style={{
                  padding: "10px",
                  textAlign: "center",
                  color: "#888",
                  fontSize: "14px"
                }}>
                  Ошибок не обнаружено
                </div>
              </PanelSectionRow>
            ) : (
              errors.slice().reverse().map((error, index) => (
                <PanelSectionRow key={index}>
                  <div style={{
                    padding: "12px",
                    backgroundColor: "rgba(255, 0, 0, 0.1)",
                    borderRadius: "4px",
                    marginBottom: "8px",
                    fontSize: "12px"
                  }}>
                    <div style={{ marginBottom: "4px", fontWeight: "bold" }}>
                      {formatTimestamp(error.timestamp)} - {error.operation}
                    </div>
                    <div style={{ marginBottom: "4px", color: "#FF6B6B" }}>
                      <strong>Тип:</strong> {error.error_type}
                    </div>
                    <div style={{ marginBottom: "4px" }}>
                      <strong>Сообщение:</strong> {error.message}
                    </div>
                    {Object.keys(error.details).length > 0 && (
                      <details style={{ marginTop: "8px" }}>
                        <summary style={{ cursor: "pointer", color: "#888" }}>
                          Детали
                        </summary>
                        <pre style={{
                          marginTop: "4px",
                          padding: "8px",
                          backgroundColor: "rgba(0, 0, 0, 0.3)",
                          borderRadius: "4px",
                          fontSize: "11px",
                          overflow: "auto"
                        }}>
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
  console.log("VPN Deck plugin initializing");

  return {
    // The name shown in various decky menus
    name: "VPN Deck",
    // The element displayed at the top of your plugin's menu
    titleView: <div className={staticClasses.Title}>VPN Deck</div>,
    // The content of your plugin's menu
    content: <Content />,
    // The icon displayed in the plugin list
    icon: <FaNetworkWired />,
    // The function triggered when your plugin unloads
    onDismount() {
      console.log("VPN Deck plugin unloading");
    },
  };
});
