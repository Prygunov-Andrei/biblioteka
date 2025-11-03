import { useState, useEffect } from 'react';
import Header from '../components/Header';
import { userAPI, librariesAPI } from '../services/api';
import './UserPage.css';

const UserPage = () => {
  const [profile, setProfile] = useState(null);
  const [libraries, setLibraries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Редактирование профиля
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    description: '',
    photo: null,
  });
  const [photoPreview, setPhotoPreview] = useState(null);
  
  // Создание новой библиотеки
  const [showCreateLibrary, setShowCreateLibrary] = useState(false);
  const [newLibrary, setNewLibrary] = useState({
    name: '',
    address: '',
    city: '',
    country: '',
    description: '',
  });
  
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [profileData, librariesData] = await Promise.all([
        userAPI.getProfile(),
        librariesAPI.getMyLibraries(),
      ]);
      setProfile(profileData);
      setFormData({
        full_name: profileData.full_name || '',
        description: profileData.description || '',
        photo: null,
      });
      setPhotoPreview(profileData.photo_url || null);
      setLibraries(Array.isArray(librariesData) ? librariesData : (librariesData.results || []));
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditMode(true);
    setFormData({
      full_name: profile?.full_name || '',
      description: profile?.description || '',
      photo: null,
    });
  };

  const handleCancel = () => {
    setEditMode(false);
    setFormData({
      full_name: profile?.full_name || '',
      description: profile?.description || '',
      photo: null,
    });
    setPhotoPreview(profile?.photo_url || null);
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData({ ...formData, photo: file });
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const updatedProfile = await userAPI.updateProfile(formData);
      setProfile(updatedProfile);
      setEditMode(false);
      setFormData({ ...formData, photo: null });
      alert('Профиль успешно обновлен!');
    } catch (error) {
      console.error('Ошибка сохранения профиля:', error);
      alert('Ошибка при сохранении профиля');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateLibrary = async () => {
    if (!newLibrary.name || !newLibrary.address) {
      alert('Пожалуйста, заполните название и адрес библиотеки');
      return;
    }
    
    setSaving(true);
    try {
      const createdLibrary = await librariesAPI.create(newLibrary);
      setLibraries([...libraries, createdLibrary]);
      setNewLibrary({
        name: '',
        address: '',
        city: '',
        country: '',
        description: '',
      });
      setShowCreateLibrary(false);
      alert('Библиотека успешно создана!');
    } catch (error) {
      console.error('Ошибка создания библиотеки:', error);
      alert('Ошибка при создании библиотеки');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLibrary = async (libraryId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту библиотеку? Книги останутся у вас, но будут без библиотеки.')) {
      return;
    }
    
    setSaving(true);
    try {
      await librariesAPI.delete(libraryId);
      setLibraries(libraries.filter(lib => lib.id !== libraryId));
      alert('Библиотека успешно удалена!');
    } catch (error) {
      console.error('Ошибка удаления библиотеки:', error);
      alert('Ошибка при удалении библиотеки');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  };

  if (loading) {
    return (
      <div className="user-page">
        <Header onLogout={handleLogout} searchQuery="" onSearch={() => {}} />
        <div className="user-page-content">
          <div className="loading">Загрузка...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-page">
      <Header onLogout={handleLogout} searchQuery="" onSearch={() => {}} />
      <div className="user-page-content">
        <div className="user-page-header">
          <h1>Моя страница</h1>
        </div>

        <div className="user-page-sections">
          {/* Редактирование профиля */}
          <section className="profile-section">
            <div className="section-header">
              <h2>Мой профиль</h2>
              {!editMode && (
                <button className="edit-button" onClick={handleEdit}>
                  Редактировать
                </button>
              )}
            </div>

            {editMode ? (
              <div className="profile-edit-form">
                <div className="form-group">
                  <label>Фото профиля</label>
                  <div className="photo-upload">
                    <div className="photo-preview">
                      {photoPreview ? (
                        <img src={photoPreview} alt="Preview" />
                      ) : (
                        <div className="photo-placeholder">
                          {formData.full_name?.[0] || profile?.user?.username?.[0] || 'U'}
                        </div>
                      )}
                    </div>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoChange}
                      className="file-input"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="full_name">ФИО</label>
                  <input
                    type="text"
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="Введите ваше полное имя"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">О себе</label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Напишите несколько слов о себе"
                    rows={5}
                  />
                </div>

                <div className="form-actions">
                  <button
                    className="save-button"
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                  </button>
                  <button
                    className="cancel-button"
                    onClick={handleCancel}
                    disabled={saving}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            ) : (
              <div className="profile-view">
                <div className="profile-photo">
                  {profile?.photo_url ? (
                    <img src={profile.photo_url} alt={profile.full_name || 'Профиль'} />
                  ) : (
                    <div className="photo-placeholder-large">
                      {profile?.full_name?.[0] || profile?.user?.username?.[0] || 'U'}
                    </div>
                  )}
                </div>
                <div className="profile-info">
                  <h3>{profile?.full_name || profile?.user?.username || 'Пользователь'}</h3>
                  <p className="username">@{profile?.user?.username}</p>
                  {profile?.description && (
                    <p className="description">{profile.description}</p>
                  )}
                </div>
              </div>
            )}
          </section>

          {/* Управление библиотеками */}
          <section className="libraries-section">
            <div className="section-header">
              <h2>Мои библиотеки</h2>
              <button
                className="add-button"
                onClick={() => setShowCreateLibrary(!showCreateLibrary)}
              >
                + Создать библиотеку
              </button>
            </div>

            {showCreateLibrary && (
              <div className="create-library-form">
                <h3>Создать новую библиотеку</h3>
                <div className="form-group">
                  <label htmlFor="lib_name">Название *</label>
                  <input
                    type="text"
                    id="lib_name"
                    value={newLibrary.name}
                    onChange={(e) => setNewLibrary({ ...newLibrary, name: e.target.value })}
                    placeholder="Например: Библиотека в Москве"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="lib_address">Адрес *</label>
                  <input
                    type="text"
                    id="lib_address"
                    value={newLibrary.address}
                    onChange={(e) => setNewLibrary({ ...newLibrary, address: e.target.value })}
                    placeholder="Полный физический адрес"
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="lib_city">Город</label>
                    <input
                      type="text"
                      id="lib_city"
                      value={newLibrary.city}
                      onChange={(e) => setNewLibrary({ ...newLibrary, city: e.target.value })}
                      placeholder="Город"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="lib_country">Страна</label>
                    <input
                      type="text"
                      id="lib_country"
                      value={newLibrary.country}
                      onChange={(e) => setNewLibrary({ ...newLibrary, country: e.target.value })}
                      placeholder="Страна"
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="lib_description">Описание</label>
                  <textarea
                    id="lib_description"
                    value={newLibrary.description}
                    onChange={(e) => setNewLibrary({ ...newLibrary, description: e.target.value })}
                    placeholder="Описание библиотеки"
                    rows={3}
                  />
                </div>
                <div className="form-actions">
                  <button
                    className="save-button"
                    onClick={handleCreateLibrary}
                    disabled={saving}
                  >
                    {saving ? 'Создание...' : 'Создать'}
                  </button>
                  <button
                    className="cancel-button"
                    onClick={() => {
                      setShowCreateLibrary(false);
                      setNewLibrary({
                        name: '',
                        address: '',
                        city: '',
                        country: '',
                        description: '',
                      });
                    }}
                    disabled={saving}
                  >
                    Отмена
                  </button>
                </div>
              </div>
            )}

            <div className="libraries-list">
              {libraries.length === 0 ? (
                <div className="empty-state">
                  <p>У вас пока нет библиотек</p>
                  <p className="hint">Создайте первую библиотеку, нажав кнопку выше</p>
                </div>
              ) : (
                libraries.map((library) => (
                  <div key={library.id} className="library-card">
                    <div className="library-info">
                      <h3>{library.name}</h3>
                      <p className="library-address">{library.address}</p>
                      {(library.city || library.country) && (
                        <p className="library-location">
                          {[library.city, library.country].filter(Boolean).join(', ')}
                        </p>
                      )}
                      {library.description && (
                        <p className="library-description">{library.description}</p>
                      )}
                      {library.books_count !== undefined && (
                        <p className="library-stats">
                          Книг в библиотеке: {library.books_count}
                        </p>
                      )}
                    </div>
                    <div className="library-actions">
                      <button
                        className="delete-button"
                        onClick={() => handleDeleteLibrary(library.id)}
                        disabled={saving}
                      >
                        Удалить
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default UserPage;

