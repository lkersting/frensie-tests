//---------------------------------------------------------------------------//
//!
//! \file   si_slab.c
//! \author Luke Kersting
//! \brief  Geometry for Electron Si-Slab verification problem
//!
//---------------------------------------------------------------------------//

void si_slab()
{
  // Set up manager of the geometry world
  gSystem->Load( "libGeom" );

  TGeoManager* geom = new TGeoManager(
                   "si_slab",
                   "Geometry for the electron Si-14 slab test prob.");

  // Create the silicon material
  TGeoMaterial* mat_1 = new TGeoMaterial( "mat_1", 28, 14, -2.329 );
  TGeoMedium* med_1 = new TGeoMedium( "med_1", 2, mat_1 );

  // Create the void material
  TGeoMaterial* void_mat = new TGeoMaterial( "void", 0, 0, 0 );
  TGeoMedium* void_med = new TGeoMedium( "void_med", 1, void_mat );

  // Create the graveyard
  TGeoMaterial* graveyard_mat = new TGeoMaterial( "graveyard", 0, 0, 0 );
  TGeoMedium* graveyard_med = new TGeoMedium( "graveyard", 3, graveyard_mat );

  // Create the silicon volume
  TGeoVolume* si_slab_volume =
    geom->MakeBox( "SLAB", med_1, 2.5, 2.5, 0.0002 );

  si_slab_volume->SetUniqueID( 1 );

  // Create the void volume
  TGeoVolume* void_cube_volume =
    geom->MakeBox( "CUBE", void_med, 2.55, 2.55, 2.0 );

  void_cube_volume->SetUniqueID( 2 );

  // Create the graveyard volume
  TGeoVolume* graveyard_volume =
    geom->MakeBox( "TERMINAL", graveyard_med, 3.5, 3.5, 3.5 );

  graveyard_volume->SetUniqueID( 3 );

  // Place the silicon slab inside of the void cube
  void_cube_volume->AddNode( si_slab_volume, 1 );

  // Place the void cube inside of the graveyard
  graveyard_volume->AddNode( void_cube_volume, 1 );
  geom->SetTopVolume( graveyard_volume );

  // Close the geometry
  geom->SetTopVisible();
  geom->CloseGeometry();

  // Draw the geometry
  // graveyard_volume->Draw();

  // Export the geometry
  geom->Export( "si_slab.root" );

  // Finished
  exit(0);
}

//---------------------------------------------------------------------------//
// end si_slab.c
//---------------------------------------------------------------------------//
