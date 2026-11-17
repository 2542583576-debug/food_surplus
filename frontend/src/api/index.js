import request from './request'

// 分类
export const getCategoryTree = () => request.get('/v1/categories')
export const createCategory = (data) => request.post('/v1/categories', data)
export const updateCategory = (id, data) => request.patch(`/v1/categories/${id}`, data)
export const moveCategory = (id, data) => request.post(`/v1/categories/${id}/move`, data)
export const deleteCategory = (id) => request.delete(`/v1/categories/${id}`)

// 属性模板
export const getTemplates = (categoryId) => request.get(`/v1/categories/${categoryId}/templates`)
export const createTemplate = (data) => request.post('/v1/categories/templates', data)
export const updateTemplate = (id, data) => request.patch(`/v1/categories/templates/${id}`, data)
export const deleteTemplate = (id) => request.delete(`/v1/categories/templates/${id}`)

// 商品
export const getProducts = (params) => request.get('/v1/products', { params })
export const createProduct = (data) => request.post('/v1/products', data)
export const updateProduct = (id, data) => request.patch(`/v1/products/${id}`, data)
export const deleteProduct = (id) => request.delete(`/v1/products/${id}`)

// 盲盒
export const getBlindBoxes = (params) => request.get('/v1/blind-boxes', { params })
export const createBlindBox = (data) => request.post('/v1/blind-boxes', data)
export const updateBlindBox = (id, data) => request.patch(`/v1/blind-boxes/${id}`, data)
export const changeBlindBoxStatus = (id, action) => request.post(`/v1/blind-boxes/${id}/status`, { action })
export const deleteBlindBox = (id) => request.delete(`/v1/blind-boxes/${id}`)

// 订单（商家端）
export const getOrders = (params) => request.get('/v1/merchant/orders', { params })
export const verifyOrder = (id, verify_code) => request.post(`/v1/merchant/orders/${id}/verify`, { verify_code })
