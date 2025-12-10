import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null);
  const user = ref<any>(null);

  function setToken(newToken: string) {
    token.value = newToken;
  }

  function setUser(newUser: any) {
    user.value = newUser;
  }

  function clearAuth() {
    token.value = null;
    user.value = null;
  }

  return {
    token,
    user,
    setToken,
    setUser,
    clearAuth,
  };
}, {
  persist: true,
});
