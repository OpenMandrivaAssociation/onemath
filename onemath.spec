%global _disable_lto 1
%global gsycl_commit 99241128f64b700392e4cfdd047caada024bf7dd

%define libname %mklibname onemath
%define devname %mklibname onemath -d

Name:		onemath
Version:	0.9
Release:	1
Summary:	oneMath SYCL BLAS (generic Intel GPU backend)
Group:		System/Libraries
License:	Apache-2.0
URL:		https://github.com/uxlfoundation/oneMath
Source0:	%{url}/archive/refs/tags/v%{version}/oneMath-v%{version}.tar.gz
Source1:	https://github.com/uxlfoundation/generic-sycl-components/archive/%{gsycl_commit}/generic-sycl-components-%{gsycl_commit}.tar.gz
Source2:	MKLConfig.cmake
Patch0:		0001-mkl-namespace-alias.patch

# Built with icpx, which is x86_64 only.

BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	intel-llvm
BuildRequires:	pkgconfig(level-zero) >= 1.32.0

%description
oneMath is the open-source SYCL math library from the UXL Foundation.
This package builds the generic BLAS backend, tuned for Intel GPUs, and
keeps the deprecated oneapi::mkl names so existing SYCL code can link it
instead of proprietary oneMKL.

The generic kernels are portable and correct. They are not as tuned as
hipBLAS or oneMKL for every shape. Pair with oneDNN for the heavier
Intel GPU matmul and attention paths.

%package -n %{libname}
Summary:	oneMath generic SYCL BLAS library
Group:		System/Libraries
Provides:	onemath = %{EVRD}

%description -n %{libname}
Shared libraries for the oneMath generic SYCL BLAS backend.

%package -n %{devname}
Summary:	Development files for oneMath
Group:		Development/C++
Requires:	%{libname}%{?_isa} = %{EVRD}
Requires:	intel-llvm%{?_isa}
Provides:	onemath-devel = %{EVRD}

%description -n %{devname}
Headers, the oneMath CMake package, and an MKLConfig.cmake shim that
maps MKL::MKL_SYCL::BLAS onto the generic oneMath BLAS library.

%prep
%autosetup -n oneMath-%{version} -p1
mkdir -p %{_builddir}/generic-sycl-components
tar -xf %{SOURCE1} -C %{_builddir}/generic-sycl-components --strip-components=1
# The fetched interface project installs cmake files and headers at the
# prefix root. The shared library from oneMath is what this package ships.
sed -i \
	-e '/install(FILES ${version_file}/,/^)/d' \
	-e '/install(DIRECTORY ${ONEMATH_SYCL_BLAS_INCLUDE}/,/^)/d' \
	-e '/install(DIRECTORY ${ONEMATH_SYCL_BLAS_INSTALL_SRC}/,/^  )/d' \
	-e '/install(EXPORT ${targets_name}/,/^)/d' \
	%{_builddir}/generic-sycl-components/onemath/sycl/blas/CMakeLists.txt

# Install libraries and CMake files under lib64, not lib.
find . -name CMakeLists.txt -print0 | xargs -0 sed -i \
	-e 's|LIBRARY DESTINATION lib|LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}|g' \
	-e 's|ARCHIVE DESTINATION lib|ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}|g' \
	-e 's|set(config_package_location "lib/cmake/${PROJECT_NAME}")|set(config_package_location "${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}")|' \
	-e 's|"lib/cmake/${PROJECT_NAME}"|"${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}"|g'

%build
# icpx device compilation rejects the distro -flto and -march flags.
_flags=$(printf '%s' "%{optflags}" | sed -E 's/-flto//g; s/-g3//g; s/-gdwarf-4//g; s/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')
_flags="$_flags -g0"
_ldflags=$(printf '%s' "%{build_ldflags}" | sed -E 's/-flto//g; s/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')
export CFLAGS="$_flags"
export CXXFLAGS="$_flags"
export LDFLAGS="$_ldflags"
export PATH="%{_libdir}/intel-llvm/bin:${PATH}"
export CC="%{_libdir}/intel-llvm/bin/icx"
export CXX="%{_libdir}/intel-llvm/bin/icpx"
export CMAKE_GENERATOR=Ninja
%cmake \
	-DENABLE_MKLCPU_BACKEND=OFF \
	-DENABLE_MKLGPU_BACKEND=OFF \
	-DENABLE_GENERIC_BLAS_BACKEND=ON \
	-DGENERIC_BLAS_TUNING_TARGET=INTEL_GPU \
	-DTARGET_DOMAINS=blas \
	-DBUILD_FUNCTIONAL_TESTS=OFF \
	-DBUILD_EXAMPLES=OFF \
	-DBUILD_DOC=OFF \
	-DFETCHCONTENT_FULLY_DISCONNECTED=ON \
	-DFETCHCONTENT_SOURCE_DIR_ONEMATH_SYCL_BLAS=%{_builddir}/generic-sycl-components
ninja -v

%install
DESTDIR=%{buildroot} ninja -C build install
mkdir -p %{buildroot}%{_libdir}/cmake/MKL
install -pm 644 %{SOURCE2} %{buildroot}%{_libdir}/cmake/MKL/MKLConfig.cmake

%files -n %{libname}
%license LICENSE
%{_libdir}/libonemath*.so.*

%files -n %{devname}
%{_includedir}/oneapi/
%{_libdir}/libonemath*.so
%{_libdir}/cmake/oneMath/
%{_libdir}/cmake/MKL/
