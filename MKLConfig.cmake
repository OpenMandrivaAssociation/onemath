# Shim so find_package(MKL) used by ggml's SYCL backend links the
# open-source oneMath generic BLAS instead of proprietary oneMKL.
# Symbols are oneapi::math::* via the oneapi::mkl namespace alias.

if(NOT TARGET MKL::MKL_SYCL::BLAS)
  add_library(MKL::MKL_SYCL::BLAS INTERFACE IMPORTED)
  get_filename_component(_onemath_prefix "${CMAKE_CURRENT_LIST_DIR}/../../.." ABSOLUTE)
  find_library(_onemath_blas_generic
    NAMES onemath_blas_generic
    PATHS "${_onemath_prefix}/lib" "${_onemath_prefix}/lib64"
    NO_DEFAULT_PATH
    REQUIRED)
  target_include_directories(MKL::MKL_SYCL::BLAS INTERFACE "${_onemath_prefix}/include")
  target_link_libraries(MKL::MKL_SYCL::BLAS INTERFACE "${_onemath_blas_generic}")
endif()

set(MKL_FOUND TRUE)
