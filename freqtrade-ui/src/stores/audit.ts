import { defineStore } from 'pinia';
import apiClient from '@/services/apiClient';
import { ref, Ref } from 'vue';
import { z } from 'zod';

const AuditLogSchema = z.object({
  id: z.number(),
  username: z.string().nullable(),
  ip_address: z.string().nullable(),
  http_method: z.string(),
  path: z.string(),
  status_code: z.number(),
  created_at: z.string().datetime(),
});

export type AuditLog = z.infer<typeof AuditLogSchema>;

export const useAuditStore = defineStore('audit', () => {
  const logs: Ref<AuditLog[]> = ref([]);
  const loading: Ref<boolean> = ref(false);
  const error: Ref<string | null> = ref(null);

  async function fetchAuditLogs() {
    loading.value = true;
    error.value = null;
    try {
      const response = await apiClient.get('/audit/logs');
      const validatedLogs = z.array(AuditLogSchema).parse(response.data);
      logs.value = validatedLogs;
    } catch (e: any) {
      if (e instanceof z.ZodError) {
        error.value = "Received invalid data from the server.";
        console.error("Zod validation error:", e.errors);
      } else {
        error.value = e.response?.data?.detail || 'Failed to fetch audit logs.';
        console.error(error.value);
      }
    } finally {
      loading.value = false;
    }
  }

  return {
    logs,
    loading,
    error,
    fetchAuditLogs,
  };
});
