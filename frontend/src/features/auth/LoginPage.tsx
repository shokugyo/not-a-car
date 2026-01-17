import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Car, Mail, Lock, User } from 'lucide-react';
import { useAuthStore } from '../../store';
import { Button } from '../../components/ui/Button';
import api from '../../api/client';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await api.register(formData.email, formData.password, formData.fullName);
        await login(formData.email, formData.password);
      }
      navigate('/');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg mb-4">
            <Car className="text-primary-600" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white">M-SUITE</h1>
          <p className="text-primary-200 mt-2">Your car works while you sleep</p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-gray-900 text-center mb-6">
            {isLogin ? 'ログイン' : '新規登録'}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  お名前
                </label>
                <div className="relative">
                  <User
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                    size={18}
                  />
                  <input
                    type="text"
                    className="input pl-10"
                    placeholder="山田 太郎"
                    value={formData.fullName}
                    onChange={(e) =>
                      setFormData({ ...formData, fullName: e.target.value })
                    }
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                メールアドレス
              </label>
              <div className="relative">
                <Mail
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  size={18}
                />
                <input
                  type="email"
                  className="input pl-10"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                パスワード
              </label>
              <div className="relative">
                <Lock
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  size={18}
                />
                <input
                  type="password"
                  className="input pl-10"
                  placeholder="********"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isLoading}
            >
              {isLoading
                ? '処理中...'
                : isLogin
                ? 'ログイン'
                : '登録する'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
            >
              {isLogin
                ? 'アカウントをお持ちでない方はこちら'
                : 'すでにアカウントをお持ちの方はこちら'}
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center text-white">
          <div>
            <div className="text-2xl mb-1">24/7</div>
            <div className="text-xs text-primary-200">常時稼働</div>
          </div>
          <div>
            <div className="text-2xl mb-1">AI</div>
            <div className="text-xs text-primary-200">収益最大化</div>
          </div>
          <div>
            <div className="text-2xl mb-1">3x</div>
            <div className="text-xs text-primary-200">収益モード</div>
          </div>
        </div>
      </div>
    </div>
  );
}
